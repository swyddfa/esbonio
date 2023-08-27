import * as vscode from 'vscode';
import { join } from "path";
import {
  ConfigurationParams,
  CancellationToken,
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  ExecutableOptions,
  ResponseError,
  State
} from "vscode-languageclient/node";

import { InitOptions } from "../common/config";
import { OutputChannelLogger } from "../common/log";
import { PythonManager } from "./python";
import { Commands, Events, Notifications } from '../common/constants';


export interface SphinxInfo {

  /**
   * A unique id used to refer to this Sphinx application instance.
   */
  id: string

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
    let command = await this.python.getCmd()
    if (!command) {
      return
    }

    // Isolate the Python interpreter from the user's environment - we brought our own.
    command.push("-S")

    let config = vscode.workspace.getConfiguration("esbonio")
    let serverDevtools = config.get<boolean>('server.enableDevTools')
    let sphinxDevtools = config.get<boolean>('sphinx.enableDevTools')

    if (serverDevtools || sphinxDevtools) {
      await this.startDevtools(command[0], ...command.slice(1), "-m", "lsp_devtools", "tui")
    }

    if (serverDevtools) {
      command.push("-m", "lsp_devtools", "agent", "--", ...command)
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
    let serverEnv: ExecutableOptions = {
      env: {
        PYTHONPATH: join(this.context.extensionPath, "bundled", "libs")
      }
    }

    let server: ServerOptions = {
      command: command[0], args: command.slice(1), options: serverEnv
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

    let initOptions: InitOptions = {
      server: {
        logLevel: config.get<string>('server.logLevel'),
        logFilter: config.get<string[]>('server.logFilter'),
        showDeprecationWarnings: config.get<boolean>('server.showDeprecationWarnings'),
        completion: {
          preferredInsertBehavior: config.get<string>('server.completion.preferredInsertBehavior')
        }
      }
    }

    let documentSelector = [
      { scheme: 'file', language: 'restructuredtext' },
    ]

    if (config.get<boolean>('server.enabledInPyFiles')) {
      documentSelector.push(
        { scheme: 'file', language: 'python' }
      )
    }

    let clientOptions: LanguageClientOptions = {
      documentSelector: documentSelector,
      initializationOptions: initOptions,
      outputChannel: this.channel,
      connectionOptions: {
        maxRestartCount: 0
      },
      middleware: {
        workspace: {
          configuration: async (params: ConfigurationParams, token: CancellationToken, next) => {
            // this.logger.debug(`workspace/configuration: ${JSON.stringify(params, undefined, 2)}`)

            let index = -1
            params.items.forEach((item, i) => {
              if (item.section === "esbonio.sphinx") {
                index = i
              }
            })

            let result = await next(params, token);
            if (result instanceof ResponseError) {
              return result
            }

            if (index < 0) {
              return result
            }

            let item = result[index]
            if (item.pythonCommand.length > 0) {
              return result
            }

            // User has not explictly configured a Python command, try and inject the
            // Python interpreter they have configured for this resource.
            let scopeUri: vscode.Uri | undefined = undefined
            let scope = params.items[index].scopeUri
            if (scope) {
              scopeUri = vscode.Uri.parse(scope)
            }
            let python = await this.python.getCmd(scopeUri)
            if (python) {
              item.pythonCommand = python
            }

            return result
          }
        }
      },
    }
    this.logger.debug(`LanguageClientOptions: ${JSON.stringify(clientOptions, null, 2)}`)
    return clientOptions
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
