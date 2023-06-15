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

/**
 * Configuration options related to completions.
 */
export interface ServerCompletionConfig {

  /**
   * Indicates how the user would prefer completion items to behave
   */
  preferredInsertBehavior?: string
}

/**
 * Represents configuration options that should be passed to the server.
 */
export interface ServerConfig {

  /**
   * Used to set the logging level of the server.
   */
  logLevel?: string

  /**
   * A list of logger names to suppress output from.
   */
  logFilter?: string[]

  /**
   * A flag to enable showing deprecation warnings.
   */
  showDeprecationWarnings?: boolean

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

}
