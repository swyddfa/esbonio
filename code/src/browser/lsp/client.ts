import * as vscode from 'vscode'
import { LanguageClient, LanguageClientOptions } from "vscode-languageclient/browser";

import { Logger } from "../core/log";


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
 * Configuration options related to completions.
 */
export interface ServerCompletionConfig {

  /**
   * Indicates how the user would prefer completion items to behave
   */
  preferredInsertBehavior: string
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

  /**
   * Server completion settings
   */
  completion: ServerCompletionConfig
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
  private worker: Worker

  private clientStartedCallbacks: Array<(params: void) => void> = []
  private clientErrorCallbacks: Array<(params: void) => void> = []
  private buildStartCallbacks: Array<(params: void) => void> = []
  private buildCompleteCallbacks: Array<(params: BuildCompleteResult) => void> = []

  constructor(
    private serverUri: vscode.Uri,
    private logger: Logger,
    private channel: vscode.OutputChannel,
  ) { }

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

    this.client = this.getClient()
    if (!this.client) {
      return
    }

    // HACK: Expose the files in the current workspace to the server.
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
      let rootUri = vscode.workspace.workspaceFolders[0].uri
      await this.syncFiles(rootUri)
    }

    try {
      this.logger.info("Starting Language Server")
      this.configureHandlers()

      await this.client.start()
      this.clientStartedCallbacks.forEach(fn => fn())

    } catch (err) {
      this.clientErrorCallbacks.forEach(fn => fn(err))
      this.logger.error(err)
    }
  }

  /**
   * This is... kind of a hack.
   *
   * We use the `vscode.workspace.fs` API to walk all the files in the workspace and
   * copy their contents into the WASM filesystem provided by pyodide.
   *
   * This requires the LS worker to have speicial support for our custom messages
   * so that it does not try and handle them as proper LSP messages.
   *
   * TODO: Investigate WASM + WASI.
   *
   */
  private async syncFiles(uri: vscode.Uri) {
    this.logger.debug(`Walking dir: ${uri}`)

    for (let [path, kind] of await vscode.workspace.fs.readDirectory(uri)) {
      if (kind === vscode.FileType.Directory) {
        await this.syncFiles(vscode.Uri.joinPath(uri, path))
        continue
      }

      let fileUri = vscode.Uri.joinPath(uri, path)
      let contents = await vscode.workspace.fs.readFile(fileUri)

      this.logger.debug(`Syncing file: ${fileUri}`)
      this.worker.postMessage({
        op: "writeFile",
        fileUri: fileUri,
        parentUri: uri,
        content: contents
      })
    }
  }


  /**
   * Restart the language server.
   */
  async restartServer() {
    let config = vscode.workspace.getConfiguration("esbonio.server")
    if (config.get("enabled")) {
      this.logger.info("==================== RESTARTING SERVER =====================")
      await this.stop()
      await this.start()
    }
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

  private getClient(): LanguageClient {
    const config = vscode.workspace.getConfiguration("esbonio")
    this.worker = new Worker(this.serverUri.toString())
    const clientOptions = this.getLanguageClientOptions(config)

    return new LanguageClient("esbonio", "Esbonio", clientOptions, this.worker)
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
      { language: 'restructuredtext' },
    ]

    if (config.get<boolean>('server.enabledInPyFiles')) {
      documentSelector.push(
        { language: 'python' }
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
    return {
      buildDir: config.get<string>('sphinx.buildDir'),
      builderName: config.get<string>('sphinx.builderName'),
      confDir: config.get<string>('sphinx.confDir'),
      // configOverrides: config.get<object>('sphinx.configOverrides'),
      doctreeDir: config.get<string>('sphinx.doctreeDir'),
      forceFullBuild: config.get<boolean>('sphinx.forceFullBuild'),
      keepGoing: config.get<boolean>('sphinx.keepGoing'),
      makeMode: config.get<boolean>('sphinx.makeMode'),
      numJobs: 1, // threading/multiprocessing not available in WASM.
      quiet: config.get<boolean>('sphinx.quiet'),
      silent: config.get<boolean>('sphinx.silent'),
      srcDir: config.get<string>("sphinx.srcDir"),
      tags: config.get<string[]>('sphinx.tags'),
      verbosity: config.get<number>('sphinx.verbosity'),
      warningIsError: config.get<boolean>('sphinx.warningIsError')
    };
  }

  onClientStart(callback: (_: void) => void) {
    this.clientStartedCallbacks.push(callback)
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
