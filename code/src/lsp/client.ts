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
 * While the ServerManager is responsible for installation and updates of the
 * Python package containing the server. The ClientManager is responsible for
 * creating the LanguageClient instance that utilmately starts the server
 * running.
 */
export class ClientManager {

  private client: LanguageClient

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
  async start() {
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

      return
    }

    this.logger.info("Starting Language Server")
    this.client.start()
    if (DEBUG) {
      // Auto open the output window when debugging
      this.client.outputChannel.show()
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

    let config = vscode.workspace.getConfiguration('esbonio')
    let command = await this.python.getCmd()

    let cache = this.context.storageUri.path

    command.push(
      "-m", "esbonio",
      "--cache-dir", join(cache, 'sphinx'),
      "--log-level", config.get<string>('server.logLevel')
    )

    if (config.get<boolean>('server.hideSphinxOutput')) {
      command.push("--hide-sphinx-output")
    }

    let logFilters = config.get<string[]>('server.logFilter')
    if (logFilters) {
      logFilters.forEach(filterName => {
        command.push("--log-filter", filterName)
      })
    }

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
    return {
      documentSelector: [
        { scheme: 'file', language: 'rst' },
        { scheme: 'file', language: 'python' }
      ]
    }
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
}