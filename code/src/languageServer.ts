import { execFile } from "child_process"
import { request, RequestOptions } from "https"
import { commands, window } from "vscode"
import { INSTALL_LANGUAGE_SERVER, UPDATE_LANGUAGE_SERVER } from "./commands"
import { getOutputLogger } from "./log"
import * as semver from "semver";

/**
 * Function to check the version of the currently installed language server.
 */
function getInstalledServerVersion(python: string): Promise<string> {
  let logger = getOutputLogger()
  let promise: Promise<string> = new Promise((resolve, reject) => {
    execFile(python, ["-m", "esbonio", "--version"], (error, stdout, stderr) => {
      if (error) {
        logger.debug(`${error.message}`)
        reject(error)
        return
      }

      let version = stdout.trim().replace('v', '')
      logger.debug(`Installed server version: ${version}`)
      resolve(version)
    })
  })

  return promise
}

/**
 * Get the version of the latest available language server.
 */
function getLatestServerVersion(): Promise<string> {
  let logger = getOutputLogger()
  let promise: Promise<string> = new Promise((resolve, reject) => {

    let options: RequestOptions = {
      host: "pypi.org",
      path: "/pypi/esbonio/json"
    }

    logger.debug("Fetching latest version from PyPi")
    request(options, (response) => {
      let body = ''

      response.on('data', (chunk) => {
        body += chunk
      })

      response.on('end', () => {
        let esbonio = JSON.parse(body)

        let version = esbonio.info.version
        logger.debug(`Latest server version: ${version}`)
        resolve(version)
      })
    }).on('error', (err) => {
      logger.debug(`Unable to fetch version from PyPi ${err.message}`)
      reject(err)
    }).end()
  })

  return promise
}

/**
 * Prompt the user to upgrade their copy of the language server.
 * TODO: Add an option that the user can click to be shown/taken to the release notes?
 */
function promptServerUpgrade(newVersion: string): Promise<boolean> {
  let promise: Promise<boolean> = new Promise((resolve, reject) => {
    let message = `Version v${newVersion} of the Esbonio language server is now availble\n` +
      "Would you like to update?"
    window.showInformationMessage(message, { title: "Yes" }, { title: "No" }).then(choice => {
      if (choice && choice.title === "Yes") {
        commands.executeCommand(UPDATE_LANGUAGE_SERVER)
      }

      // It doesn't matter if the user rejects the upgrade, we can still run the existing
      // install.
      resolve(true)
    })
  })

  return promise;
}

/**
 * Prompt the user to install the language server.
 */
function promptServerInstall(): Promise<boolean> {
  let logger = getOutputLogger()
  let promise: Promise<boolean> = new Promise((resolve, reject) => {

    let message = "The Esbonio language server is not installed.\n" +
      "Would you like to install it?"

    window.showWarningMessage(message, { title: "Yes" }, { title: "No" }).then(res => {
      if (res && res.title === "Yes") {
        logger.info("Installing language server...")
        commands.executeCommand(INSTALL_LANGUAGE_SERVER).then(_ => {
          resolve(true)
        })
        return
      }
      // Server not installed and user denied the prompt to install.
      // No point in trying to start the server.
      resolve(false)
    })

  })

  return promise
}


/**
 * Given the python interpreter to use, try and ensure a language server is present.
 *
 * First this will check to see if we have a version installed. If not it will prompt
 * the user to install it.
 *
 * If there is a version installed, it will then check to see if an update available
 * giving the user the option to upgrade if necessary.
 *
 * At any point if we're unable to bootstrap a version of the server, the promise
 * returned from this function will resolve to false, indicating we should not attempt
 * to start it.
 *
 * TODO: Add a configurable option around how updates are handled.
 *       - 'never':  Don't bother checking for updates, user can still update manually if they wish
 *       - 'prompt': Check for updates, prompt before applying (Current behavior)
 *       - 'auto':   Automatically check for and apply updates.
 * TODO: If checking for updates, only check once a week/month/<time period>
 *
 * @param python Path to the python interpreter we should be using.
 */
export function bootstrapLanguageServer(python: string): Promise<boolean> {
  let logger = getOutputLogger()
  let promise: Promise<boolean> = new Promise((resolve, reject) => {

    getInstalledServerVersion(python).then(installedVersion => {

      getLatestServerVersion().then(latestVersion => {
        if (semver.lt(installedVersion, latestVersion)) {
          promptServerUpgrade(latestVersion).then(res => resolve(res))
          return
        }

        logger.info("Language server is up to date.")
        resolve(true)
      }).catch(err => {
        logger.info(`Unable to fetch latest server version.`)
        resolve(true)
      })

    }).catch(err => {
      if (err.message.includes("No module named esbonio")) {
        promptServerInstall().then(res => resolve(res))
        return
      }
      reject(err)
    })
  })

  return promise
}
