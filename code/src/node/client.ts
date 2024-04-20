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
  pythonCommand: string[]

  /**
   * The sphinx-build command in use
   */
  buildCommand: string[]

  /**
   * The working directory of the client
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

  private client?: LanguageClient

  private devtools?: vscode.TaskExecution

  private handlers: Map<string, any[]>

  constructor(
    private logger: OutputChannelLogger,
    private python: PythonManager,
    private context: vscode.ExtensionContext,
    private channel: vscode.OutputChannel,
  ) {
    this.handlers = new Map()

    // Restart server implementation
    context.subscriptions.push(
      vscode.commands.registerCommand(Commands.RESTART_SERVER, async () => await this.restartServer())
    )

    // Unset devtools task when it finishes.
    context.subscriptions.push(
      vscode.tasks.onDidEndTask((event) => {
        if (event.execution === this.devtools) {
          this.devtools = undefined
        }
      })
    )

    // React to environment changes in the Python extension
    python.addHandler(Events.PYTHON_ENV_CHANGE, (_event: ActiveEnvironmentPathChangeEvent) => {
      this.client?.sendNotification("workspace/didChangeConfiguration", { settings: null })
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
      this.client = await this.getStdioClient()
    } catch (err) {
      this.logger.error(`${err}`)
      return
    }

    if (!this.client) {
      return
    }

    try {
      this.logger.info("Starting Language Server")
      await this.client.start()
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

    if (this.client && this.client.state === State.Running) {
      this.callHandlers(Events.SERVER_STOP, undefined)
      await this.client.stop()
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
    const sphinxDevtools = config.get<boolean>('sphinx.enableDevTools')
    const lsp_devtools = this.resolveCommand("lsp-devtools")?.trim()

    const command = []
    if (serverDevtools && lsp_devtools) {
      // Requires lsp-devtools to be on the user's PATH
      command.push(lsp_devtools, "agent", "--")
    }

    let pythonCommand = await this.python.getCmd()
    if (!pythonCommand) {
      return
    }

    // Isolate the Python interpreter from the user's environment - we brought our own.
    command.push(...pythonCommand, "-S")

    if ((serverDevtools || sphinxDevtools) && lsp_devtools) {
      // Requires lsp-devtools to be on the user's PATH.
      await this.startDevtools(lsp_devtools, "inspect")
    }

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
      this.getLanguageClientOptions(config)
    )
    this.registerHandlers(client)
    return client
  }


  public scrollView(line: number) {
    this.client?.sendNotification(Notifications.VIEW_SCROLL, { line: line })
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
  private getLanguageClientOptions(config: vscode.WorkspaceConfiguration): LanguageClientOptions {



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
      middleware: {
        workspace: {
          configuration: async (params: ConfigurationParams, token: CancellationToken, next) => {
            // this.logger.debug(`workspace/configuration: ${JSON.stringify(params, undefined, 2)}`)
            let result = await next(params, token);
            if (result instanceof ResponseError) {
              return result
            }

            result.forEach(async (config, i) => {
              await this.injectPython(params, i, config)
              this.stripNulls(config)
            })
            return result
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

  /**
   * Inject the user's configured Python interpreter into the configuration.
   */
  private async injectPython(params: ConfigurationParams, index: number, config: any) {
    if (params.items[index].section !== "esbonio") {
      return
    }

    if (config?.sphinx?.pythonCommand?.length > 0) {
      return
    }

    // User has not explictly configured a Python command, try and inject the
    // Python interpreter they have configured for this resource.
    let scopeUri: vscode.Uri | undefined
    let scope = params.items[index].scopeUri
    if (scope) {
      scopeUri = vscode.Uri.parse(scope)
    }
    let python = await this.python.getCmd(scopeUri)
    if (python) {
      config.sphinx.pythonCommand = python
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

  private async startDevtools(command: string, ...args: string[]) {

    if (this.devtools) {
      return
    }

    const task = new vscode.Task(
      { type: 'esbonio-devtools' },
      vscode.TaskScope.Workspace,
      "lsp-devtools",
      "esbonio",
      new vscode.ProcessExecution(
        command,
        args,
        {
          env: {
            PYTHONPATH: join(this.context.extensionPath, "bundled", "libs")
          }
        }
      ),
    )
    this.devtools = await vscode.tasks.executeTask(task)
  }
}
