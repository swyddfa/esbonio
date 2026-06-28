import { execSync } from "child_process";
import * as vscode from 'vscode';
import { ActiveEnvironmentPathChangeEvent } from '@vscode/python-extension';
import {
  CancellationToken,
  ConfigurationParams,
  Executable,
  LanguageClient,
  LanguageClientOptions,
  ResponseError,
  ShowDocumentParams,
  State,
  TextDocumentFilter
} from "vscode-languageclient/node";

import { Logger } from "../common/log";
import { PythonManager } from "./python";
import { Commands, Events, Notifications, Server } from '../common/constants';


export interface SphinxClientConfig {

  /**
   * The python command used to launch the client
   */
  pythonCommand: PythonCommand

  /**
   * The sphinx-build command in use
   */
  buildCommand: string[]

}

export interface PythonCommand {
  /**
   * The command that was invoked
   */
  command: string[]

  /**
   * The environment variables the command was launched with
   */
  env: { [key: string]: string }

  /**
   * The working directory the command was launched in
   */
  cwd: string
}

export interface ClientCreatedNotification {
  /**
   * A unique id for this client
   */
  id: string

  /**
   * The configuration scope at which the client was created
   */
  scope: string

  /**
   * The final configuration
   */
  config: SphinxClientConfig

  /**
   * The client process id
   */
  pid: number
}

/**
 * The payload of a ``sphinx/clientErrored`` notification
 */
export interface ClientErroredNotification {

  /**
   * A unique id for the client
   */
  id: string

  /**
   * Short description of the error.
   */
  error: string

  /**
   * Detailed description of the error.
   */
  detail: string
}


export interface ClientDestroyedNotification {
  /**
   * A unique id for this client
   */
  id: string
}

export interface SphinxInfo {


  /**
   * Sphinx's version number
   */
  version: string

  /**
   * The version of Python Sphinx is running under
   */
  python: string

  /**
   * The Sphinx application object's confdir
   */
  conf_dir: string


  /**
   * The Sphinx application object's outdir
   */
  build_dir: string


  /**
   * The current builder's name
   */
  builder_name: string

  /**
   * The Sphinx application object's srcdir
   */
  src_dir: string
}

export interface AppCreatedNotification {

  /**
   * A unique id for this client
   */
  id: string

  /**
   * Details about the created application.
   */
  application: SphinxInfo
}

export class EsbonioClient {

  public server?: LanguageClient | 'starting'

  private handlers: Map<string, any[]>

  private extensionUri: vscode.Uri

  constructor(
    private logger: Logger,
    private python: PythonManager,
    context: vscode.ExtensionContext,
    private channel: vscode.OutputChannel,
  ) {
    this.handlers = new Map()
    this.extensionUri = context.extensionUri

    // Restart server implementation
    context.subscriptions.push(
      vscode.commands.registerCommand(Commands.RESTART_SERVER, async () => await this.restartServer())
    )

    // React to environment changes in the Python extension
    python.addHandler(Events.PYTHON_ENV_CHANGE, (_event: ActiveEnvironmentPathChangeEvent) => {

      if (!this.server) {
        logger.debug("No current server, starting from Python environment change handler.")
        this.start()
        return
      }

      if (this.server === 'starting') {
        logger.debug("Server is currently starting, ignoring Python environment change.")
        return
      }

      let states = [State.Starting]
      logger.debug(`Server state is ${State[this.server.state]}`)

      if (!states.includes(this.server.state)) {
        logger.debug(`(Re)starting from Python environment change handler.`)
        this.start()
      }
    })
  }

  public addHandler(event: string, handler: any) {
    if (this.handlers.has(event)) {
      this.handlers.get(event)?.push(handler)
    } else {
      this.handlers.set(event, [handler])
    }
  }

  /**
   * Start the language server.
   */
  async start(): Promise<void> {

    if (this.server === 'starting') {
      this.logger.debug("Server is already starting, doing nothing.")
      return
    }

    let states = [State.Running, State.Starting]
    if (this.server && states.includes(this.server.state)) {
      this.logger.debug("Server is starting or already running, doing nothing.")
      return
    }

    try {
      this.server = 'starting'
      this.server = await this.getStdioClient()
    } catch (err) {
      this.logger.error(`${err}`)
      this.server = undefined
      return
    }

    if (!this.server) {
      return
    }

    try {
      this.logger.info("Starting Language Server")
      await this.server.start()
      this.callHandlers(Events.SERVER_START, undefined)
    } catch (err) {
      this.logger.error(`${err}`)
    }
  }


  /**
   * Restart the language server
   */
  async restartServer() {
    let config = vscode.workspace.getConfiguration("esbonio.server")
    if (config.get("enabled")) {
      this.logger.info("Restarting server...")
      await this.stop()
      await this.start()
    }
  }

  /**
   * Stop the language server.
   */
  async stop() {

    if (this.server === 'starting') {
      this.logger.debug("Server is currently starting and cannot be stopped.")
      return
    }

    if (this.server && this.server.state === State.Running) {
      this.logger.info("Stopping Language Server")
      this.callHandlers(Events.SERVER_STOP, undefined)
      await this.server.stop()
      this.server = undefined
    }

    return
  }

  /**
   * Return a LanguageClient configured to communicate with the server over stdio.
   */
  private async getStdioClient(): Promise<LanguageClient | undefined> {
    const config = vscode.workspace.getConfiguration("esbonio")

    let pythonCommand = await this.python.getServerOptions()
    if (!pythonCommand) {
      let message = `Unable to start the Esbonio server as a compatible Python interpreter could not be found.
        Please select an interpreter using the Python extension, or set the esbonio.server.pythonCommand setting.`

      let result = await vscode.window.showErrorMessage(message, 'Select Interpreter')
      if (result === 'Select Interpreter') {
        await vscode.commands.executeCommand(Commands.PYTHON_SELECT_INTERPRETER)
      }

      return
    }

    let serverCommand: Executable = {
      command: pythonCommand.command,
      args: [...pythonCommand.args || [], ...config.get<string[]>("server.launchArgs") || []],
    }

    if (pythonCommand.options?.env) {
      serverCommand.options = { env: pythonCommand.options.env }
    }


    this.logger.debug(`Server start command: ${serverCommand.command} ${serverCommand.args?.join(" ") || ""}`)
    if (serverCommand.options?.env?.PYTHONPATH) {
      this.logger.debug(`Server PYTHONPATH: '${serverCommand.options.env.PYTHONPATH}'`)
    }

    let client = new LanguageClient(
      'esbonio',
      'Esbonio Language Server',
      serverCommand,
      this.getLanguageClientOptions(pythonCommand, config)
    )
    this.registerHandlers(client)
    return client
  }


  public scrollView(uri: vscode.Uri, line: number) {

    if (!this.server || this.server === 'starting') {
      return
    }

    this.server.sendNotification(Notifications.VIEW_SCROLL, {
      uri: uri.toString(), line: line
    })
  }


  /**
   * Register any additional method handlers on the language client.
   */
  private registerHandlers(client: LanguageClient) {

    let methods = [
      Notifications.SCROLL_EDITOR,
      Notifications.SPHINX_APP_CREATED,
      Notifications.SPHINX_CLIENT_CREATED,
      Notifications.SPHINX_CLIENT_ERRORED,
      Notifications.SPHINX_CLIENT_DESTROYED,
    ]

    for (let method of methods) {
      client.onNotification(method, (params) => {
        this.callHandlers(method, params)
      })
    }
  }

  /**
   * Returns the LanguageClient options that are common to both modes of
   * transport.
   */
  private getLanguageClientOptions(pythonCommand: Executable, config: vscode.WorkspaceConfiguration): LanguageClientOptions {
    let documentSelector = config.get<TextDocumentFilter[]>("server.documentSelector")
    if (!documentSelector || documentSelector.length === 0) {
      documentSelector = Server.DEFAULT_SELECTOR
    }

    let command = [pythonCommand.command]
    if (pythonCommand.args) {
      command.push(...pythonCommand.args)
    }
    if (!command.includes("-S")) {
      command.push("-S")  // Isolates the interpreter from its normal environment.
    }

    let clientOptions: LanguageClientOptions = {
      documentSelector: documentSelector,
      outputChannel: this.channel,
      connectionOptions: {
        maxRestartCount: 0
      },
      initializationOptions: {
        // Fallback sphinx configuration
        sphinx: {
          pythonCommand: {
            command: command,
            env: {
              PYTHONPATH: vscode.Uri.joinPath(this.extensionUri, "bundled", "env").fsPath
            }
          }
        }
      },
      middleware: {
        workspace: {
          configuration: async (params: ConfigurationParams, token: CancellationToken, next) => {
            // this.logger.debug(`workspace/configuration: ${JSON.stringify(params, undefined, 2)}`)
            let result = await next(params, token);
            if (result instanceof ResponseError) {
              return result
            }

            result.forEach((config) => {
              this.stripNulls(config)
            })
            return result
          }
        },
        window: {
          showDocument: async (params: ShowDocumentParams, next) => {
            // this.logger.debug(`window/showDocument: ${JSON.stringify(params, undefined, 2)}`)
            this.callHandlers("window/showDocument", { params: params, default: next })
            return { success: true }
          }
        }
      },
    }
    this.logger.debug(`LanguageClientOptions: ${JSON.stringify(clientOptions, null, 2)}`)
    return clientOptions
  }

  /**
   * Strip any `null` values from the returned configuration.
   */
  private stripNulls(config: any) {
    for (let k of Object.keys(config)) {
      if (config[k] === null) {
        delete config[k]
      } else if (typeof config[k] === 'object') {
        this.stripNulls(config[k])
      }
    }
  }

  private callHandlers(method: string, params: any) {
    this.handlers.get(method)?.forEach(handler => {
      try {
        handler(params)
      } catch (err) {
        this.logger.error(`Error in '${method}' notification handler: ${err}`)
      }
    })
  }
}
