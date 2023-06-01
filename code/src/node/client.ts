import * as vscode from 'vscode';
import { join } from "path";
import { LanguageClient, LanguageClientOptions, ServerOptions, ExecutableOptions } from "vscode-languageclient/node";

import { SphinxConfig, InitOptions } from "../common/config";
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

    let startupModule = config.get<string>("server.startupModule") || "esbonio"
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
      sphinx: this.getSphinxOptions(config),
      server: {
        logLevel: config.get<string>('server.logLevel'),
        logFilter: config.get<string[]>('server.logFilter'),
        hideSphinxOutput: config.get<boolean>('server.hideSphinxOutput'),
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
      outputChannel: this.channel
    }
    this.logger.debug(`LanguageClientOptions: ${JSON.stringify(clientOptions, null, 2)}`)
    return clientOptions
  }

  private getSphinxOptions(config: vscode.WorkspaceConfiguration): SphinxConfig {

    let buildDir = config.get<string>('sphinx.buildDir')
    let numJobs = config.get<number>('sphinx.numJobs')

    if (!buildDir && this.context.storageUri) {
      let cache = this.context.storageUri.path
      buildDir = join(cache, 'sphinx')
    }

    return {
      buildDir: buildDir,
      builderName: config.get<string>('sphinx.builderName'),
      confDir: config.get<string>('sphinx.confDir'),
      configOverrides: config.get<object>('sphinx.configOverrides'),
      doctreeDir: config.get<string>('sphinx.doctreeDir'),
      forceFullBuild: config.get<boolean>('sphinx.forceFullBuild'),
      keepGoing: config.get<boolean>('sphinx.keepGoing'),
      makeMode: config.get<boolean>('sphinx.makeMode'),
      numJobs: numJobs === 0 ? 'auto' : numJobs,
      quiet: config.get<boolean>('sphinx.quiet'),
      silent: config.get<boolean>('sphinx.silent'),
      srcDir: config.get<string>("sphinx.srcDir"),
      tags: config.get<string[]>('sphinx.tags'),
      verbosity: config.get<number>('sphinx.verbosity'),
      warningIsError: config.get<boolean>('sphinx.warningIsError')
    };
  }

  async stop() {

    if (this.client) {
      await this.client.stop()
    }

    return
  }
}
