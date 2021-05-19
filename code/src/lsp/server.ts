import { request, RequestOptions } from "https";
import * as semver from "semver";
import * as vscode from "vscode";

import { Commands, Server } from "../constants";
import { Logger } from "../log";
import { PythonCommand, PythonManager } from "./python";

/**
 * Class responsible for managing the Language server. i.e. installation & updates of the
 * esbonio Python package.
 */
export class ServerManager {

  LAST_UPDATE = "server.lastUpdate"

  constructor(
    private logger: Logger,
    private python: PythonManager,
    private context: vscode.ExtensionContext
  ) {
    context.subscriptions.push(
      vscode.commands.registerCommand(Commands.INSTALL_SERVER, this.installServer, this)
    )
    context.subscriptions.push(
      vscode.commands.registerCommand(Commands.UPDATE_SERVER, this.updateServer, this)
    )
  }

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
  async bootstrap(retry: number = 1): Promise<string | undefined> {

    if (!await this.checkPythonVersion()) {
      return undefined
    }

    let currentVersion = await this.getServerVersion()
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
    if (semver.lt(currentVersion, Server.REQUIRED_VERSION)) {
      let message = `Your current version of the Esbonio language server (v${currentVersion}) is outdated and
      not compatible with this version of the extension.

      Please upgrade to at least version v${Server.REQUIRED_VERSION}.`

      let response = await vscode.window.showErrorMessage(message, { title: "Update Server" })
      if (!response || response.title !== "Update Server") {
        return undefined
      }

      await this.updateServer()
      return this.bootstrap(retry - 1)
    }

    // Otherwise, do the regular update checks
    return await this.checkForUpdates(currentVersion)
  }

  /**
   * Install the language server into the currently configured Python environment
   */
  async installServer(): Promise<null> {
    let command: PythonCommand = {
      name: "Install Language Server",
      args: ["-m", "pip", "install", `esbonio>=${Server.REQUIRED_VERSION}`],
    }

    await this.python.runCommand(command)

    // Store today's date so that the installation counts as an update.
    let today = new Date(Date.now())
    this.context.workspaceState.update(this.LAST_UPDATE, today.toISOString())

    return
  }

  /**
   * Update the language server into the currently configured Python environment
   */
  async updateServer(): Promise<null> {
    let command: PythonCommand = {
      name: "Update Language Server",
      args: ["-m", "pip", "install", "--upgrade", `esbonio>=${Server.REQUIRED_VERSION}`],
    }

    await this.python.runCommand(command)

    let today = new Date(Date.now())
    this.context.workspaceState.update(this.LAST_UPDATE, today.toISOString())

    return
  }

  private async checkForUpdates(currentVersion: string, retry: number = 1): Promise<string | undefined> {

    let config = vscode.workspace.getConfiguration("esbonio")
    let updateBehavior = config.get<string>('server.updateBehavior')
    let updateFrequency = config.get<string>('server.updateFrequency')

    if (updateFrequency === 'never') {
      this.logger.debug("Update checks are disabled")
      return currentVersion
    }

    let lastUpdateStr = this.context.workspaceState.get(this.LAST_UPDATE, "1970-01-01")
    this.logger.debug(`Last update was ${lastUpdateStr}`)

    let today = new Date(Date.now())
    let lastUpdate = new Date(Date.parse(lastUpdateStr))

    if (!shouldUpdate(updateFrequency, today, lastUpdate)) {
      return currentVersion
    }

    let latestVersion = await this.getLatestVersion()
    if (!semver.lt(currentVersion, latestVersion)) {
      return currentVersion
    }

    if (shouldPromptUpdate(updateBehavior, currentVersion, latestVersion)) {
      let message = `Version v${latestVersion} of the Esbonio language server is now available.
      Would you like to update?`

      let response = await vscode.window.showInformationMessage(message, { title: "Yes" }, { title: "No" })
      if (!response || response.title !== "Yes") {
        return currentVersion
      }
    }

    await this.updateServer()
    return await this.bootstrap(retry - 1)
  }

  /**
   * Get the version of the currently installed language server.
   *
   * If the server is not installed it will attempt to install it
   * according to the user's configured instal behavior.
   */
  private async getServerVersion(retry: number = 1): Promise<string | undefined> {
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
      let config = vscode.workspace.getConfiguration("esbonio")
      let installBehavior = config.get<string>('server.installBehavior')

      if (!await shouldInstall(installBehavior)) {
        return undefined
      }

      await this.installServer()
      return await this.getServerVersion(retry - 1)
    }
  }

  /**
   * Check PyPi for the latest released version of the language server.
   */
  private getLatestVersion(): Promise<string> {
    return new Promise((resolve, reject) => {

      let options: RequestOptions = {
        host: 'pypi.org',
        path: '/pypi/esbonio/json'
      }

      this.logger.debug("Fetching latest version from PyPi")
      request(options, (response) => {
        let body = ''
        response.on('data', (chunk) => body += chunk)

        response.on('end', () => {
          let esbonio = JSON.parse(body)

          let version = esbonio.info.version
          this.logger.debug(`Latest version: ${version}`)

          let today = new Date(Date.now())
          this.context.workspaceState.update(this.LAST_UPDATE, today.toISOString())

          resolve(version)
        })
      }).on('error', (err) => {
        this.logger.debug(`Unable to fetch version from PyPi ${err.message}`)
        reject(err)
      }).end()
    })
  }

  /**
   * Ensure that the configured Python environment is compatible with the server.
   */
  private async checkPythonVersion(): Promise<string | undefined> {
    let pythonVersion = await this.python.getVersion()
    if (!pythonVersion) {
      let message = "No Python envrionment configured."
      await vscode.window.showErrorMessage(message, { title: "Close" })
      return undefined
    }

    if (semver.lt(pythonVersion, Server.REQUIRED_PYTHON)) {
      let message = `Your configured Python version is v${pythonVersion} which is incompatible with the
      Esbonio Lanuage Server.

      Please choose an environment that has a Python version of at least v${Server.REQUIRED_PYTHON}`
      await vscode.window.showErrorMessage(message, { title: "Close" })

      // TODO: Add a "pick interpreter" button that will automatically call the following
      //       command. (Of course this should only be added if the python extension is available)
      // await vscode.commands.executeCommand("python.setInterpreter")
      return undefined
    }

    return pythonVersion
  }
}

export async function shouldInstall(installBehavior: string): Promise<boolean> {
  if (installBehavior === "nothing") {
    return false
  }

  if (installBehavior === "automatic") {
    return true
  }

  let message = `The Esbonio Language Server is not installed in your current environment.
  Would you like to install it?`

  let response = await vscode.window.showWarningMessage(message, { title: "Yes" }, { title: "No" })
  return response && (response.title === "Yes")
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
