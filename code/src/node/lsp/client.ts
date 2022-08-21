import * as net from "net";
import * as vscode from "vscode";

import { join } from "path";
import { LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient/node";

import { Commands } from "../constants";
import { PythonManager } from "./python";
import { ServerManager } from "./server";
import { Logger } from "../log";


const DEBUG = process.env.VSCODE_LSP_DEBUG === "true"

/**
 * Represents the current sphinx configuration / configuration options
 * that should be passed to sphinx on creation.
 */
export interface SphinxConfig {

  /**
   * The directory where Sphinx's build output should be stored.
   */
  buildDir?: string

  /**
   * The name of the builder to use.
   */
  builderName?: string

  /**
   * The directory containing the project's 'conf.py' file.
   */
  confDir?: string

  /**
   * Any overriden conf.py options.
   */
  configOverrides?: object,

  /**
   * The directory in which to store Sphinx's doctree cache
   */
  doctreeDir?: string,

  /**
   * Flag to force a full build of the documentation on startup.
   */
  forceFullBuild?: boolean

  /**
   * Flag to continue building when errors generated from warnings are encountered.
   */
  keepGoing?: boolean

  /**
   * Flag controlling if the server should behave like `sphinx-build -M ...`
   */
  makeMode?: boolean

  /**
   * The number of parallel jobs to use
   */
  numJobs?: number | string

  /**
   * Hide standard Sphinx output messages.
   */
  quiet?: boolean

  /**
   * Hide all Sphinx output.
   */
  silent?: boolean

  /**
   * The source dir containing the *.rst files for the project.
   */
  srcDir?: string

  /**
   * Tags to enable during a build.
   */
  tags?: string[]

  /**
   * The verbosity of Sphinx's output.
   */
  verbosity?: number

  /**
   * Treat any warnings as errors.
   */
  warningIsError?: boolean
}

export interface SphinxInfo extends SphinxConfig {

  /**
   * The equivalent `sphinx-build` command for the current configuration
   */
  command?: string[]

  /**
   * Sphinx's version number.
   */
  version?: string
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

  /**
   * A flag to enable showing deprecation warnings.
   */
  showDeprecationWarnings: boolean
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

export interface BuildCompleteResult {
  /**
   * The options representing the server's config.
   */
  config: { server: ServerConfig, sphinx: SphinxInfo },

  /**
   * Flag indicating if the previous build resulted in an error.
   */
  error: boolean,

  /**
   * The number of warnings emitted in the previous build.
   */
  warnings: number,
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
  public sphinxInfo?: SphinxInfo

  private client: LanguageClient
  private allowRestarts = true

  private clientStartCallbacks: Array<(params: void) => void> = []
  private clientErrorCallbacks: Array<(params: void) => void> = []
  private buildStartCallbacks: Array<(params: void) => void> = []
  private buildCompleteCallbacks: Array<(params: BuildCompleteResult) => void> = []

  constructor(
    private logger: Logger,
    private python: PythonManager,
    private server: ServerManager,
    private channel: vscode.OutputChannel,
    private context: vscode.ExtensionContext
  ) {
    context.subscriptions.push(vscode.commands.registerCommand(Commands.RESTART_SERVER, this.restartServer, this))
    context.subscriptions.push(vscode.commands.registerCommand(Commands.COPY_BUILD_COMMAND, this.copyBuildCommand, this))
    context.subscriptions.push(vscode.commands.registerCommand(Commands.SET_BUILD_COMMAND, this.setBuildCommand, this))
    context.subscriptions.push(vscode.commands.registerCommand(Commands.SELECT_BUILDDIR, selectBuildDir))
    context.subscriptions.push(vscode.commands.registerCommand(Commands.SELECT_CONFDIR, selectConfDir))
    context.subscriptions.push(vscode.commands.registerCommand(Commands.SELECT_SRCDIR, selectSrcDir))

    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(this.configChanged, this))
  }

  async stop() {

    if (this.client) {
      await this.client.stop()
    }

    return
  }

  /**
   * Start the language client.
   */
  async start(): Promise<void> {

    if (DEBUG) {
      this.client = await this.getTcpClient()
    } else {
      this.client = await this.getStdioClient()
    }

    if (!this.client) {
      let message = "Unable to start language server.\n" +
        "See output window for more details"
      vscode.window.showErrorMessage(message, { title: "Show Output" }).then(opt => {
        if (opt && opt.title === "Show Output") {
          this.channel.show()
        }
      })
      return
    }

    try {
      this.logger.info("Starting Language Server")
      this.client.start()
      this.clientStartCallbacks.forEach(fn => fn())

      if (DEBUG) {
        // Auto open the output window when debugging
        this.client.outputChannel.show()
      }

      await this.client.onReady()
      this.configureHandlers()

    } catch (err) {
      this.clientErrorCallbacks.forEach(fn => fn(err))
      this.logger.error(err)
    }
  }

  /**
   * Restart the language server.
   */
  async restartServer() {
    let config = vscode.workspace.getConfiguration("esbonio.server")
    if (this.allowRestarts && config.get("enabled")) {
      this.logger.info("==================== RESTARTING SERVER =====================")
      await this.stop()
      await this.start()
    }
  }

  async copyBuildCommand() {
    if (!this.sphinxInfo) {
      return
    }

    await vscode.env.clipboard.writeText(this.sphinxInfo.command.join(' '))
  }

  /**
   * Prompt the user for the new build command and update the config accordingly.
   */
  async setBuildCommand() {

    let config = vscode.workspace.getConfiguration("esbonio")
    let currentCliArgs = await this.sphinxConfigToCLI(config);
    let cliArgs = await vscode.window.showInputBox({
      value: currentCliArgs,
      placeHolder: '-M html ...',
      prompt: 'Set sphinx-build arguments',
    })

    if (!cliArgs) {
      // User cancelled, no need to show an error.
      return
    }

    let sphinxConfig = await this.sphinxCLIToConfig(cliArgs);
    if (!sphinxConfig) {
      // Actually an error we should care about.
      let res = await vscode.window.showErrorMessage("Unable to update sphinx-build command", "Show Output")
      if (res == 'Show Output') {
        this.channel.show()
      }

      return
    }

    await this.setSphinxConfig(sphinxConfig, config);
  }

  /**
   * Update the user's sphinx configuration to match the given configuration.
   *
   * @param sphinxConfig The SphinxConfig to use
   * @param config The "esbonio" configuration namespace
   */
  private async setSphinxConfig(sphinxConfig: SphinxConfig, config: vscode.WorkspaceConfiguration) {
    // Based on [1] it would appear that there is no way to bulk update configuration values.
    // Instead, we'll just have to turn off the restart mechanism until this is complete.
    //
    // [1]: https://github.com/microsoft/vscode/issues/63616
    this.allowRestarts = false;

    for (const [key, value] of Object.entries(sphinxConfig)) {
      try {
        await config.update(`sphinx.${key}`, value);
      } catch (err) {
        this.logger.error(`Unable to set ${key} = ${value}\n${err}`);
      }
    }

    this.allowRestarts = true;
    await this.restartServer();
  }

  /**
   * Convert a set of sphinx-build cli arguments into the equivalent SphinxConfig.
   *
   * @param cliArgs The arguments to pass to 'sphinx-build'
   * @returns
   */
  private async sphinxCLIToConfig(cliArgs: string): Promise<SphinxConfig | undefined> {

    try {
      let result = await this.python.execCommand({
        args: [
          '-m', 'esbonio.lsp.sphinx.cli', 'config', '--', ...cliArgs.split(' '),
        ]
      });
      this.logger.debug(result.stdout);
      return JSON.parse(result.stdout);

    } catch (err) {
      this.logger.debug(`Unable to obtain Sphinx Config\n${err}`)
      return undefined
    }
  }

  /**
   * Convert the current sphinx configuration into the equivalent set of `sphinx-build`
   * cli arguments.
   *
   * @param config The "esbonio" configuration namespace
   * @returns
   */
  private async sphinxConfigToCLI(config: vscode.WorkspaceConfiguration): Promise<string | undefined> {
    let currentConfig = this.getSphinxOptions(config);

    try {
      let currentArgs = await this.python.execCommand({
        args: [
          '-m', 'esbonio.lsp.sphinx.cli', 'config', '--to-cli', JSON.stringify(currentConfig)
        ]
      });
      this.logger.debug(`Current build args, ${currentArgs.stdout}`);
      return currentArgs.stdout;

    } catch (err) {
      this.logger.error(`Unable to determine current 'sphinx-build' arugments:\n${err}`)
      return undefined
    }
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
    let config = vscode.workspace.getConfiguration("esbonio")

    let startupModule = config.get<string>("server.startupModule")

    // Entry point can either be a script, or it can be a python module.
    if (startupModule.endsWith(".py") || startupModule.includes("/") || startupModule.includes("\\")) {
      command.push(startupModule)
    } else {
      command.push("-m", startupModule)
    }

    config.get<string[]>('server.includedModules').forEach(mod => {
      command.push('--include', mod)
    })

    config.get<string[]>('server.excludedModules').forEach(mod => {
      command.push('--exclude', mod)
    })

    this.logger.debug(`Server start command: ${command.join(" ")}`)

    return new LanguageClient(
      'esbonio', 'Esbonio Language Server',
      { command: command[0], args: command.slice(1) },
      this.getLanguageClientOptions(config)
    )
  }

  /**
   * Return a LanguageClient configured to communicate with the server over TCP.
   * Typically used while debugging.
   */
  private async getTcpClient(): Promise<LanguageClient | undefined> {
    let config = vscode.workspace.getConfiguration("esbonio")

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
      this.getLanguageClientOptions(config)
    )
  }

  private configureHandlers() {

    this.client.onNotification("esbonio/buildStart", params => {
      this.logger.debug("Build start.")
      this.buildStartCallbacks.forEach(fn => fn())
    })

    this.client.onNotification("esbonio/buildComplete", (result: BuildCompleteResult) => {
      this.logger.debug(`Build complete ${JSON.stringify(result, null, 2)}`)
      this.sphinxInfo = result.config.sphinx
      this.buildCompleteCallbacks.forEach(fn => {
        fn(result)
      })
    })
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
        showDeprecationWarnings: config.get<boolean>('server.showDeprecationWarnings')
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

    if (!buildDir) {
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

  /**
   * Listen to changes in the user's configuration and decide if we should
   * restart the language server.
   */
  private async configChanged(event: vscode.ConfigurationChangeEvent) {
    this.logger.debug(`ConfigurationChangeEvent`)

    let config = vscode.workspace.getConfiguration("esbonio")
    if (!config.get("server.enabled")) {
      await this.stop()
      return
    }


    let conditions = [
      event.affectsConfiguration("esbonio"),
      !config.get<string>('server.pythonPath') && event.affectsConfiguration("python.pythonPath")
    ]

    if (conditions.some(i => i)) {
      await this.restartServer()
    }
  }

  onClientStart(callback: (_: void) => void) {
    this.clientStartCallbacks.push(callback)
  }

  onClientError(callback: (_: void) => void) {
    this.clientErrorCallbacks.push(callback)
  }

  onBuildComplete(callback: (result: BuildCompleteResult) => void) {
    this.buildCompleteCallbacks.push(callback)
  }

  onBuildStart(callback: (_: void) => void) {
    this.buildStartCallbacks.push(callback)
  }
}

async function selectBuildDir() {
  return await selectFolder("buildDir")
}


async function selectConfDir() {
  return await selectFolder("confDir")
}


async function selectSrcDir() {
  return await selectFolder("srcDir")
}


async function selectFolder(name: string) {
  let rootUri
  let config = vscode.workspace.getConfiguration("esbonio.sphinx")

  let rootFolders = vscode.workspace.workspaceFolders
  if (rootFolders) {
    rootUri = rootFolders[0].uri
  }

  let uri = await vscode.window.showOpenDialog({ canSelectFolders: true, defaultUri: rootUri, canSelectMany: false })
  if (!uri) {
    return
  }

  config.update(name, uri[0].path, vscode.ConfigurationTarget.Workspace)
}
