import * as vscode from 'vscode';
import { join } from "path";
import {
  ConfigurationParams,
  CancellationToken,
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  ExecutableOptions,
  ResponseError
} from "vscode-languageclient/node";

import { InitOptions } from "../common/config";
import { OutputChannelLogger } from "../common/log";
import { PythonManager } from "./python";


export class EsbonioClient {

  private client?: LanguageClient

  constructor(
    private logger: OutputChannelLogger,
    private python: PythonManager,
    private context: vscode.ExtensionContext,
    private channel: vscode.OutputChannel,
  ) { }

  /**
    * Start the language client.
    */
  async start(): Promise<void> {

    this.client = await this.getStdioClient()

    if (!this.client) {
      return
    }

    try {
      this.logger.info("Starting Language Server")
      await this.client.start()

    } catch (err) {
      this.logger.error(`${err}`)
    }
  }

  /**
  * Return a LanguageClient configured to communicate with the server over stdio.
  * Typically used in production.
  */
  private async getStdioClient(): Promise<LanguageClient | undefined> {


    let command = await this.python.getCmd()
    if (!command) {
      return
    }

    let config = vscode.workspace.getConfiguration("esbonio")

    // if (config.get<boolean>('server.enableDevTools')) {
    //   command.push("-m", "lsp_devtools", "agent", "--", ...command)
    // }

    let startupModule = config.get<string>("server.startupModule") || "esbonio.server"
    // let includedModules = config.get<string[]>('server.includedModules') || []
    // let excludedModules = config.get<string[]>('server.excludedModules') || []

    // Entry point can either be a script, or it can be a python module.
    if (startupModule.endsWith(".py") || startupModule.includes("/") || startupModule.includes("\\")) {
      command.push(startupModule)
    } else {
      command.push("-m", startupModule)
    }

    // includedModules.forEach(mod => {
    //   command?.push('--include', mod)
    // })

    // excludedModules.forEach(mod => {
    //   command?.push('--exclude', mod)
    // })

    this.logger.debug(`Server start command: ${command.join(" ")}`)
    let serverEnv: ExecutableOptions = {
      env: {
        PYTHONPATH: join(this.context.extensionPath, "bundled", "libs")
      }
    }

    let server: ServerOptions = {
      command: command[0], args: command.slice(1), options: serverEnv
    }

    return new LanguageClient(
      'esbonio',
      'Esbonio Language Server',
      server,
      this.getLanguageClientOptions(config)
    )
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
      middleware: {
        workspace: {
          configuration: async (params: ConfigurationParams, token: CancellationToken, next) => {
            this.logger.debug(`workspace/configuration: ${JSON.stringify(params, undefined, 2)}`)

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

  async stop() {

    if (this.client) {
      await this.client.stop()
    }

    return
  }
}
