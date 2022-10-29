import { RequestOptions } from "https";
import * as semver from "semver";

import { Server } from "../constants";
import { EditorIntegrations, WorkspaceState } from "../core/editor";
import { Logger } from "../core/log";
import { PythonCommand, PythonManager } from "./python";

/**
 * Used to indicate what the next course of action should be.
 */
enum NextAction {

  /**
   * The process was cancelled or an error occurred and we should abort
   */
  Abort = 0,

  /**
   * Something changed or we couldn't make progress, we should try again
   */
  Retry = 1,

  /**
   * All is well, carry on.
   */
  Continue = 2
}


/**
 * Class responsible for managing the Language server. i.e. installation & updates of the
 * esbonio Python package.
 */
export class ServerManager {

  static LAST_UPDATE = "server.lastUpdate"

  constructor(
    private editor: EditorIntegrations,
    private logger: Logger,
    private python: PythonManager,
    private state: WorkspaceState,
  ) { }

  /**
   * Ensure a compatible copy of the language server is present in the current environment.
   *
   * First this will check to see if there is a version already installed. If not, the user
   * will be prompted to install it. If there is a version installed, it will check for updates
   * according to the update policy in the user's settings.
   *
   * If we're unable to obtain any version of the server, the returned promise will resolve to
   * `undefined` indicating we should not try to start the server.
   */
  async bootstrap(
    requiredPythonVersion: string,
    requiredServerVersion: string,
    today: Date,
    retry: number = 1
  ): Promise<string | undefined> {

    if (!await this.checkPythonVersion(requiredPythonVersion)) {
      return undefined
    }

    let currentVersion = await this.getServerVersion(requiredServerVersion, today)
    if (!currentVersion) {
      return undefined
    }

    // PEP 440 dev release numbers (https://www.python.org/dev/peps/pep-0440/#developmental-releases)
    // are not compatible with semver. To allow people to test dev builds with the extension we
    // need to transform the version number to be semver compatible.
    if (currentVersion.includes(".dev")) {
      currentVersion = currentVersion.replace(".dev", "-dev.")
      this.logger.debug(`Semver compatible version: ${currentVersion}`)
    }

    // Check to see if the current version satisfies the minimum version requirements, we may
    // have to force an upgrade.
    this.logger.info(`Server version '${currentVersion}'`)
    if (semver.lt(currentVersion, requiredServerVersion)) {
      let message = `Your current version of the Esbonio language server (v${currentVersion}) is outdated and
      not compatible with this version of the extension.

      Please upgrade to at least version v${requiredServerVersion}.`

      let response = await this.editor.showErrorMessage(message, { title: "Update Server" }, { title: "Disable Server" })
      if (response && response.title == "Update Server") {
        await this.updateServer(requiredServerVersion, today)
        return this.bootstrap(requiredPythonVersion, requiredServerVersion, today, retry - 1)
      }

      if (response && response.title == "Disable Server") {
        let config = this.editor.getConfiguration("esbonio")
        await config.update("server.enabled", false)
      }

      return undefined
    }

    // Otherwise, do the regular update checks
    let result = await this.checkForUpdates(requiredServerVersion, currentVersion, today)
    if (typeof result === 'string') {
      return result
    }

    switch (result) {
      case NextAction.Continue:
        return await this.bootstrap(requiredPythonVersion, requiredServerVersion, today, retry - 1)
      case NextAction.Retry:
        return await this.bootstrap(requiredPythonVersion, requiredServerVersion, today, retry)
      default:
        return undefined
    }
  }

  /**
   * Install the language server into the currently configured Python environment
   */
  async installServer(requiredServerVersion: string, today: Date): Promise<null> {
    let command: PythonCommand = {
      name: "Install Language Server",
      args: ["-m", "pip", "install", `esbonio>=${requiredServerVersion}`],
    }

    await this.python.runCommand(command)

    // Store today's date so that the installation counts as an update.
    this.state.update(ServerManager.LAST_UPDATE, today.toISOString())

    return
  }

  /**
   * Update the language server into the currently configured Python environment
   */
  async updateServer(requiredServerVersion: string, today: Date): Promise<null> {
    let command: PythonCommand = {
      name: "Update Language Server",
      args: ["-m", "pip", "install", "--upgrade", `esbonio>=${requiredServerVersion}`],
    }

    await this.python.runCommand(command)
    this.state.update(ServerManager.LAST_UPDATE, today.toISOString())

    return
  }

  async checkForUpdates(requiredServerVersion: string, currentVersion: string, today: Date, retry: number = 1): Promise<string | NextAction> {

    let config = this.editor.getConfiguration("esbonio")
    let updateBehavior = config.get<string>('server.updateBehavior')
    let updateFrequency = config.get<string>('server.updateFrequency')

    if (updateFrequency === 'never') {
      this.logger.debug("Update checks are disabled")
      return currentVersion
    }

    let lastUpdateStr = this.state.get(ServerManager.LAST_UPDATE, "1970-01-01")
    this.logger.debug(`Last update was ${lastUpdateStr}`)

    let lastUpdate = new Date(Date.parse(lastUpdateStr))

    if (!shouldUpdate(updateFrequency, today, lastUpdate)) {
      return currentVersion
    }

    let latestVersion: string

    try {
      latestVersion = await this.getLatestVersion(today)
    } catch (err) {
      this.logger.debug(`Unable to fetch version from PyPi ${err.message}`)
      this.logger.debug(`Continuing with current version.`)
      return currentVersion
    }

    if (!semver.lt(currentVersion, latestVersion)) {
      return currentVersion
    }

    if (shouldPromptUpdate(updateBehavior, currentVersion, latestVersion)) {
      let message = `Version v${latestVersion} of the Esbonio language server is now available.
      Would you like to update?`

      let response = await this.editor.showInformationMessage(message, { title: "Yes" }, { title: "No" })
      if (!response || response.title !== "Yes") {
        return currentVersion
      }
    }

    await this.updateServer(requiredServerVersion, today)
    return NextAction.Continue
  }

  /**
   * Get the version of the currently installed language server.
   *
   * If the server is not installed it will attempt to install it
   * according to the user's configured install behavior.
   */
  async getServerVersion(requiredServerVersion: string, today: Date, retry: number = 1): Promise<string | undefined> {
    let command: PythonCommand = {
      args: ["-m", "esbonio", "--version"]
    }

    try {
      let { stdout } = await this.python.execCommand(command)
      let version = stdout.trim().replace("v", "")

      this.logger.debug(`Server version '${version}'`)
      return version
    } catch (err) {
      this.logger.debug(`${err.message}`)

      if (retry <= 0 || !err.message.includes("No module named esbonio")) {
        this.logger.error(`${err}`)
        return undefined
      }

      // Try installing the language server.
      let config = this.editor.getConfiguration("esbonio")
      let installBehavior = config.get<string>('server.installBehavior')
      let nextAction = await this.shouldInstall(installBehavior)

      switch (nextAction) {
        case NextAction.Continue:
          await this.installServer(requiredServerVersion, today)
          return await this.getServerVersion(requiredServerVersion, today, retry - 1)
        case NextAction.Retry:
          return await this.getServerVersion(requiredServerVersion, today, retry)
        default:
          return undefined
      }

    }
  }

  async shouldInstall(installBehavior: string): Promise<NextAction> {
    if (installBehavior === "nothing") {
      return NextAction.Abort
    }

    if (installBehavior === "automatic") {
      return NextAction.Continue
    }

    let message = `The Esbonio Language Server is not installed in your current environment.
    Would you like to install it?`

    let options = [{ title: "Yes" }, { title: "No" }]
    if (await this.python.hasPythonExtension()) {
      options.push({ title: "Switch Environments" })
    }

    options.push({ title: 'Disable Server' })
    let response = await this.editor.showWarningMessage(message, ...options)

    if (response && (response.title === "Yes")) {
      return NextAction.Continue
    }

    if (response && (response.title === "Switch Environments")) {
      await this.python.selectEnvironment()
      return NextAction.Retry
    }

    if (response && (response.title === "Disable Server")) {
      let config = this.editor.getConfiguration("esbonio")
      await config.update("server.enabled", false)
    }

    return NextAction.Abort
  }

  /**
   * Check PyPi for the latest released version of the language server.
   */
  private async getLatestVersion(today: Date): Promise<string> {

    let options: RequestOptions = {
      host: 'pypi.org',
      path: '/pypi/esbonio/json'
    }

    this.logger.debug("Fetching latest version from PyPi")
    let res = await this.editor.httpGet(options)
    let esbonio = JSON.parse(res)

    let version = esbonio.info.version
    this.logger.debug(`Latest version: ${version}`)

    this.state.update(ServerManager.LAST_UPDATE, today.toISOString())

    return version
  }

  /**
   * Ensure that the configured Python environment is compatible with the server.
   */
  async checkPythonVersion(requiredVersion: string): Promise<string | undefined> {
    let pythonVersion = await this.python.getVersion()
    let hasPythonExt = await this.python.hasPythonExtension()


    if (!pythonVersion) {
      let message = "No Python envrionment configured."
      let options = []

      if (hasPythonExt) {
        options.push({ title: "Select Environment" })
      }

      let response = await this.editor.showErrorMessage(message, ...options)
      if (response && response.title === "Select Environment") {
        await this.python.selectEnvironment()
        return await this.checkPythonVersion(requiredVersion)
      }

      return undefined
    }

    if (semver.lt(pythonVersion, requiredVersion)) {
      let options = []
      let message = `Your configured Python version v${pythonVersion} is incompatible with the
      Esbonio Lanuage Server.

      Please choose an environment that has a Python version >= v${requiredVersion}`

      if (hasPythonExt) {
        options.push({ title: "Select Environment" })
      }

      let response = await this.editor.showErrorMessage(message, ...options)
      if (response && response.title === "Select Environment") {
        await this.python.selectEnvironment()
        return await this.checkPythonVersion(requiredVersion)
      }

      return undefined
    }

    return pythonVersion
  }
}

export function shouldPromptUpdate(updateBehavior: string, currentVersion: string, latestVersion: string) {
  if (updateBehavior === "automatic") {
    return false
  }

  if (updateBehavior === "promptAlways") {
    return true
  }

  // promptMajor -- only prompt if the next release is a major version bump.
  let version = semver.parse(currentVersion)
  return !semver.satisfies(latestVersion, `<${version.major + 1}`)
}

export function shouldUpdate(frequency: string, today: Date, lastUpdate: Date): boolean {

  /*
    Yes, taking the difference of dates like this is not an accurate way of determining
    how many calendar days have elapsed etc. But for this use case as long as we get in
    the right ballpark it should be sufficient.
   */
  let timeDelta = today.valueOf() - lastUpdate.valueOf()

  let day = 1000 * 60 * 60 * 24
  let week = day * 7
  let month = day * 30

  let conds = [
    frequency === 'daily' && timeDelta >= day,
    frequency === 'weekly' && timeDelta >= week,
    frequency === 'monthly' && timeDelta >= month
  ]

  return conds.some(i => i)
}
