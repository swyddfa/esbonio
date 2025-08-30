import { execSync } from "child_process";
import * as vscode from 'vscode';
import { ActiveEnvironmentPathChangeEvent } from '@vscode/python-extension';
import { join } from "path";
import {
  CancellationToken,
  ConfigurationParams,
  LanguageClient,
  LanguageClientOptions,
  ResponseError,
  ServerOptions,
  ShowDocumentParams,
  State,
  TextDocumentFilter
} from "vscode-languageclient/node";

import { OutputChannelLogger } from "../common/log";
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

  public server?: LanguageClient

  private handlers: Map<string, any[]>

  private extensionUri: vscode.Uri

  constructor(
    private logger: OutputChannelLogger,
    private python: PythonManager,
    private context: vscode.ExtensionContext,
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

      let states = [State.Running, State.Starting]
      if (!this.server || !states.includes(this.server.state)) {
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

    try {
      this.server = await this.getStdioClient()
    } catch (err) {
      this.logger.error(`${err}`)
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

    if (this.server && this.server.state === State.Running) {
      this.callHandlers(Events.SERVER_STOP, undefined)
      await this.server.stop()
    }

    return
  }

  /**
   * Return a LanguageClient configured to communicate with the server over stdio.
   */
  private async getStdioClient(): Promise<LanguageClient | undefined> {
    const config = vscode.workspace.getConfiguration("esbonio")
    const debugServer = config.get<boolean>('server.debug')
    const serverDevtools = config.get<boolean>('server.enableDevTools')
    const lsp_devtools = this.resolveCommand("lsp-devtools")?.trim()

    const command = []
    if (serverDevtools && lsp_devtools) {
      // Requires lsp-devtools to be on the user's PATH
      command.push(lsp_devtools, "agent", "--")
    }

    let pythonCommand = await this.python.getCmd()
    if (!pythonCommand) {
      let message = `Unable to start the Esbonio server as a compatible Python interpreter could not be found.
        Please select an interpreter using the Python extension, or set the esbonio.server.pythonPath setting.`

      let result = await vscode.window.showErrorMessage(message, 'Select Interpreter')
      if (result === 'Select Interpreter') {
        await vscode.commands.executeCommand(Commands.PYTHON_SELECT_INTERPRETER)
      }

      return
    }

    // Isolate the Python interpreter from the user's environment - we brought our own.
    command.push(...pythonCommand, "-S")

    if (debugServer) {
      let debugCommand = await this.python.getDebugerCommand()
      command.push("-Xfrozen_modules=off", ...debugCommand)
    }

    let startupModule = config.get<string>("server.startupModule") || "esbonio.server"
    let includedModules = config.get<string[]>('server.includedModules') || []
    let excludedModules = config.get<string[]>('server.excludedModules') || []

    // Entry point can either be a script, or it can be a python module.
    if (startupModule.endsWith(".py") || startupModule.includes("/") || startupModule.includes("\\")) {
      command.push(startupModule)
    } else {
      command.push("-m", startupModule)
    }

    includedModules.forEach(mod => {
      command?.push('--include', mod)
    })

    excludedModules.forEach(mod => {
      command?.push('--exclude', mod)
    })

    this.logger.debug(`Server start command: ${command.join(" ")}`)
    const serverEnv: any = {
      PYTHONPATH: join(this.context.extensionPath, "bundled", "libs")
    };

    // Passthrough any environment variables we haven't set ourselves..
    Object.keys(process.env).forEach((key) => {
      if (!serverEnv[key]) {
        serverEnv[key] = process.env[key]
      }
    });

    let server: ServerOptions = {
      command: command[0], args: command.slice(1), options: {
        env: serverEnv
      }
    }

    let client = new LanguageClient(
      'esbonio',
      'Esbonio Language Server',
      server,
      this.getLanguageClientOptions(pythonCommand, config)
    )
    this.registerHandlers(client)
    return client
  }


  public scrollView(uri: vscode.Uri, line: number) {
    this.server?.sendNotification(Notifications.VIEW_SCROLL, {
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
  private getLanguageClientOptions(pythonCommand: string[], config: vscode.WorkspaceConfiguration): LanguageClientOptions {
    let documentSelector = config.get<TextDocumentFilter[]>("server.documentSelector")
    if (!documentSelector || documentSelector.length === 0) {
      documentSelector = Server.DEFAULT_SELECTOR
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
            command: [...pythonCommand, "-S"],
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

  private resolveCommand(command: string): string | undefined {
    // TODO: Windows support
    try {
      let result = execSync(`command -v ${command}`)
      return result.toString()
    } catch (err) {
      this.logger.debug(`Unable to resolve command ${command}: ${err}`)
      return undefined
    }
  }

}
