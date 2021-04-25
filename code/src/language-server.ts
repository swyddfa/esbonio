import * as child_process from 'child_process'
import * as semver from "semver";
import * as vscode from "vscode";

import { request, RequestOptions } from "https"
import { join } from "path";
import { promisify } from "util";
import { LanguageClientOptions } from 'vscode-languageclient';
import { Executable, LanguageClient, ServerOptions } from "vscode-languageclient/node";

import { INSTALL_LANGUAGE_SERVER, UPDATE_LANGUAGE_SERVER } from "./commands"
import { getOutputLogger } from "./log"


const MIN_PYTHON = "3.6.0"
const LAST_UPDATE = "server.lastUpdate"
const execFile = promisify(child_process.execFile)


/**
 * Class that handles initializing the language server.
 */
export class LanguageServerBootstrap {

  private logger

  constructor(public python: string, public context: vscode.ExtensionContext) {
    this.logger = getOutputLogger()
  }

  /**
   * Try and ensure a Language server is present in the current environment.
   *
   * First this will check to see if there is a version already installed. If not, the user
   * will be prompted to install it. If there is a version installed, it will check for updates
   * according to the update policy as per the user's settings.
   *
   * If we're unable to obtain any version of the server, the promise returned by this method
   * will resolve to false, indicating that we should not try to start it.
   */
  async ensureLanguageServer(): Promise<string> {

    let pythonVersion = await this.checkPython()
    if (!pythonVersion) {
      return ""
    }

    let currentVersion = await this.checkInstalled()
    if (!currentVersion) {
      return ""
    }

    let latestVersion = await this.checkForUpdates(currentVersion)
    if (!semver.lt(currentVersion, latestVersion)) {
      return currentVersion
    }

    let updateBehavior = vscode.workspace.getConfiguration("esbonio").get<string>("server.updateBehavior")
    if (shouldPromptUpdate(updateBehavior, currentVersion, latestVersion)) {
      let message = `Version v${latestVersion} of the Esbonio language server is now available\n` +
        "Would you like to update?"

      let respone = await vscode.window.showInformationMessage(message, { title: "Yes" }, { title: "No" })
      if (!respone || respone.title !== "Yes") {
        return currentVersion
      }
    }

    await vscode.commands.executeCommand(UPDATE_LANGUAGE_SERVER)
    return latestVersion
  }

  /**
   * Check for any updates and return the latest version.
   *
   * This respects the value of the `esbonio.server.updateFrequency` user settting. If
   * the value is `never` then it simply returns the current version. Otherwise it will
   * check in `context.workspaceState` to see if an update is due.
   */
  async checkForUpdates(currentVersion: string): Promise<string> {
    let updateFrequency = vscode.workspace.getConfiguration("esbonio").get<string>("server.updateFrequency")
    if (updateFrequency === 'never') {
      this.logger.debug("Update checks are disabled")
      return currentVersion
    }

    let lastUpdateStr = this.context.workspaceState.get(LAST_UPDATE, "1970-01-01")
    this.logger.debug(`Last update was ${lastUpdateStr}`)

    let today = new Date(Date.now())
    let lastUpdate = new Date(Date.parse(lastUpdateStr))

    if (shouldUpdate(updateFrequency, today, lastUpdate)) {
      let latestVersion = await this.getLatestVersion()

      let today = new Date(Date.now())
      this.context.workspaceState.update(LAST_UPDATE, today.toISOString())

      return latestVersion
    }

    return currentVersion
  }

  /**
   * Checks to see if the Language Server is currently installed.
   *
   * If it is, this method will return the version number. Otherwise will prompt
   * the user to install it.
   */
  async checkInstalled(): Promise<string> {
    try {
      let version = await getInstalledVersion(this.python)
      this.logger.debug(`Current version: ${version}`)

      return version
    } catch (err) {
      this.logger.debug(`${err.message}`)

      if (!err.message.includes("No module named esbonio")) {
        this.logger.debug(`Unknown error ${err}`)
        return ""
      }

      let config = vscode.workspace.getConfiguration("esbonio")
      let installBehavior = config.get<string>('server.installBehavior')

      let tryInstall = await shouldInstall(installBehavior)
      if (!tryInstall) {
        return ""
      }

      this.logger.debug("Installing language server,")
      await vscode.commands.executeCommand(INSTALL_LANGUAGE_SERVER)

      try {
        let version = await getInstalledVersion(this.python)

        // Store todays date so the installation counts as an update
        let today = new Date(Date.now())
        this.context.workspaceState.update(LAST_UPDATE, today.toISOString())

        return version;
      } catch (err) {
        this.logger.debug(`Installation failed ${err}`)
        return ""
      }

    }
  }

  /**
   * Check that the configured Python is compatible with the Language Server.
   */
  async checkPython() {

    try {
      let { stdout } = await execFile(this.python, ["--version"])
      let version = stdout.trim().replace("Python ", "")

      this.logger.debug(`Python version ${version}`)

      // Ensure we extracted a valid version number
      if (!semver.parse(version)) {
        this.logger.debug("Unable to confirm Python version.")
        return ""
      }

      if (semver.lt(version, MIN_PYTHON)) {
        let message = `Configured Python has version v${version} which is incompatible with the
        Esbonio Language Server.

        Please choose an environment that has a Python version of at least v${MIN_PYTHON}`
        await vscode.window.showErrorMessage(message, { title: "Close" })

        return ""
      }

      return version

    } catch (err) {
      this.logger.debug("Unable to confirm Python version.")
      this.logger.debug(`${err.message}`)

      return ""
    }
  }

  /**
   * Return an appropriate language client instance.
   */
  getLanguageClient(): LanguageClient {
    let config = vscode.workspace.getConfiguration('esbonio')

    let pythonArgs = [
      '-m', 'esbonio',
      '--cache-dir', join(this.context.storagePath, 'sphinx'),
      '--log-level', config.get<string>('server.logLevel')
    ]

    if (config.get<boolean>('server.hideSphinxOutput')) {
      pythonArgs.push("--hide-sphinx-output")
    }

    let logFilters = config.get<string[]>('server.logFilter')
    if (logFilters) {
      logFilters.forEach(filterName => {
        pythonArgs.push("--log-filter", filterName)
      })
    }

    let exe: Executable = {
      command: this.python,
      args: pythonArgs
    }

    this.logger.debug(`Server start command: ${JSON.stringify(exe)}`)
    let serverOptions: ServerOptions = exe

    let clientOptions: LanguageClientOptions = {
      documentSelector: [
        { scheme: 'file', language: 'rst' },
        { scheme: 'file', language: 'python' }
      ]
    }

    return new LanguageClient('esbonio', 'Esbonio Language Server', serverOptions, clientOptions)
  }

  getLatestVersion(): Promise<string> {
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
          resolve(version)
        })
      }).on('error', (err) => {
        this.logger.debug(`Unable to fetch version from PyPi ${err.message}`)
        reject(err)
      }).end()
    })
  }
}

async function getInstalledVersion(python: string): Promise<string> {
  let { stdout } = await execFile(python, ["-m", "esbonio", "--version"])
  let version = stdout.trim().replace("v", "")

  return version
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