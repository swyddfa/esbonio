import * as net from "net";
import * as vscode from "vscode";

import { join } from "path";
import { LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient/node";

import { Commands } from "../constants";
import { getOutputLogger, Logger } from "../log";
import { PythonManager } from "./python";
import { ServerManager } from "./server";


const DEBUG = process.env.VSCODE_LSP_DEBUG === "true"

/**
 * Represents the current sphinx configuration / configuration options
 * that should be passed to sphinx on creation.
 */
export interface SphinxConfig {

  /**
   * Sphinx's version number.
   */
  version?: string

  /**
   * The directory containing the project's 'conf.py' file.
   */
  confDir?: string

  /**
   * The source dir containing the *.rst files for the project.
   */
  srcDir?: string

  /**
   * The directory where Sphinx's build output should be stored.
   */
  buildDir?: string

  /**
   * The name of the builder to use.
   */
  builderName?: string

}

/**
 * Represents configuration options that should be passed to the server.
 */
export interface ServerConfig {

  /**
   * Used to set the logging level of the server.
   */
  logLevel: string

  /**
   * A list of logger names to suppress output from.
   */
  logFilter?: string[]

  /**
   * A flag to indicate if Sphinx build output should be omitted from the log.
   */
  hideSphinxOutput: boolean
}

/**
 * The initialization options we pass to the server on startup.
 */
export interface InitOptions {

  /**
   * Language server specific options
   */
  server: ServerConfig

  /**
   * Sphinx specific options
   */
  sphinx: SphinxConfig
}

/**
 * While the ServerManager is responsible for installation and updates of the
 * Python package containing the server. The EsbonioClient is responsible for
 * creating the LanguageClient instance that utilmately starts the server
 * running.
 */
export class EsbonioClient {

  /**
   * If present, this represents the current configuration of the Sphinx instance
   * managed by the Language server.
   */
  public sphinxConfig?: SphinxConfig

  private client: LanguageClient
  private statusBar: vscode.StatusBarItem

  private buildCompleteCallback

  constructor(
    private logger: Logger,
    private python: PythonManager,
    private server: ServerManager,
    private context: vscode.ExtensionContext
  ) {
    context.subscriptions.push(
      vscode.commands.registerCommand(Commands.RESTART_SERVER, this.restartServer, this)
    )
    context.subscriptions.push(
      vscode.workspace.onDidChangeConfiguration(this.configChanged, this)
    )

    this.statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left)
    context.subscriptions.push(this.statusBar)
  }

  async stop() {
    if (!this.client) {
      return
    }

    return await this.client.stop()
  }

  /**
   * Start the language client.
   */
  async start(): Promise<void> {
    this.statusBar.text = "$(sync~spin) Starting."
    this.statusBar.show()
    if (DEBUG) {
      this.client = await this.getTcpClient()
    } else {
      this.client = await this.getStdioClient()
    }

    if (!this.client) {
      let message = "Unable to start language server.\n" +
        "See output window for more details"
      vscode.window.showErrorMessage(message, { title: "Show Output" }).then(opt => {
        if (opt.title === "Show Output") {
          getOutputLogger().show()
        }
      })
      this.statusBar.text = "$(error) Failed."
      return
    }

    try {
      this.logger.info("Starting Language Server")
      this.client.start()

      if (DEBUG) {
        // Auto open the output window when debugging
        this.client.outputChannel.show()
      }

      await this.client.onReady()
      this.client.onNotification("esbonio/sphinxConfiguration", params => {
        this.sphinxConfig = params
        this.statusBar.text = `$(check) Sphinx v${this.sphinxConfig.version}`
      })

      this.client.onNotification("esbonio/buildComplete", params => {
        this.logger.debug("Build complete")
        if (this.buildCompleteCallback) {
          this.buildCompleteCallback()
        }
      })

      return
    } catch (err) {
      this.statusBar.text = "$(error) Failed."
    }
  }

  /**
   * Restart the language server.
   */
  async restartServer() {
    this.logger.info("Stopping Language Server")

    if (this.client) {
      await this.client.stop()
    }

    await this.start()
  }

  /**
   * Return a LanguageClient configured to communicate with the server over stdio.
   * Typically used in production.
   */
  private async getStdioClient(): Promise<LanguageClient | undefined> {

    let version = await this.server.bootstrap()
    if (!version) {
      return undefined
    }

    let command = await this.python.getCmd()
    command.push(
      "-m", "esbonio",
    )

    this.logger.debug(`Server start command: ${command.join(" ")}`)

    return new LanguageClient(
      'esbonio', 'Esbonio Language Server',
      { command: command[0], args: command.slice(1) },
      this.getLanguageClientOptions()
    )
  }

  /**
   * Return a LanguageClient configured to communicate with the server over TCP.
   * Typically used while debugging.
   */
  private async getTcpClient(): Promise<LanguageClient | undefined> {

    let serverOptions: ServerOptions = () => {
      return new Promise((resolve) => {
        const clientSocket = new net.Socket()
        clientSocket.connect(8421, "127.0.0.1", () => {
          resolve({
            reader: clientSocket,
            writer: clientSocket
          })
        })
      })
    }

    return new LanguageClient(
      "esbonio", "Esbonio Language Server",
      serverOptions,
      this.getLanguageClientOptions()
    )
  }

  /**
   * Returns the LanguageClient options that are common to both modes of
   * transport.
   */
  private getLanguageClientOptions(): LanguageClientOptions {

    let cache = this.context.storageUri.path
    let config = vscode.workspace.getConfiguration("esbonio")

    let initOptions: InitOptions = {
      sphinx: {
        srcDir: config.get<string>("sphinx.srcDir"),
        confDir: config.get<string>('sphinx.confDir'),
        buildDir: join(cache, 'sphinx')
      },
      server: {
        logLevel: config.get<string>('server.logLevel'),
        logFilter: config.get<string[]>('server.logFilter'),
        hideSphinxOutput: config.get<boolean>('server.hideSphinxOutput')
      }
    }

    let clientOptions: LanguageClientOptions = {
      documentSelector: [
        { scheme: 'file', language: 'rst' },
        { scheme: 'file', language: 'python' }
      ],
      initializationOptions: initOptions
    }
    this.logger.debug(`LanguageClientOptions: ${JSON.stringify(clientOptions)}`)
    return clientOptions
  }

  /**
   * Listen to changes in the user's configuration and decide if we should
   * restart the language server.
   */
  private async configChanged(event: vscode.ConfigurationChangeEvent) {
    this.logger.debug(`ConfigurationChangeEvent`)

    let config = vscode.workspace.getConfiguration("esbonio")

    let conditions = [
      event.affectsConfiguration("esbonio"),
      !config.get<string>('server.pythonPath') && event.affectsConfiguration("python.pythonPath")
    ]

    if (conditions.some(i => i)) {
      await this.restartServer()
    }
  }

  onBuildComplete(callback) {
    this.buildCompleteCallback = callback
  }
}