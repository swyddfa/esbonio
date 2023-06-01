import * as vscode from 'vscode'

import { OutputChannelLogger } from "../common/log";
import { IExtensionApi } from './python-ext-api';


const PYTHON_EXTENSION = "ms-python.python"


export class PythonManager {
  constructor(private logger: OutputChannelLogger) { }

  async getCmd(): Promise<string[] | undefined> {
    let userPython = vscode.workspace.getConfiguration("esbonio").get<string>("server.pythonPath")
    if (userPython) {

      // Support for ${workspaceRoot}/...
      let match = userPython.match(/^\${(\w+)}/)
      if (match && (match[1] === 'workspaceRoot' || match[1] === 'workspaceFolder')) {
        let workspaceRoot = ""
        let workspaceFolders = vscode.workspace.workspaceFolders

        if (workspaceFolders) {
          workspaceRoot = workspaceFolders[0].uri.fsPath
        }

        userPython = userPython.replace(match[0], workspaceRoot)
      }

      this.logger.debug(`Using user configured Python: ${userPython}`)
      return [userPython]
    }

    let python = await this.getPythonExtension()
    if (!python) {
      return
    }

    let activeEnvPath = python.environments.getActiveEnvironmentPath()
    this.logger.debug(`Using environment ${activeEnvPath.id}: ${activeEnvPath.path}`)

    let activeEnv = await python.environments.resolveEnvironment(activeEnvPath)
    if (!activeEnv) {
      this.logger.debug("Unable to resolve environment")
      return
    }

    let pythonUri = activeEnv.executable.uri
    if (!pythonUri) {
      this.logger.debug("URI of Python executable is undefined...")
      return
    }

    return [pythonUri.fsPath]
  }

  /**
   * Ensures that if the Python extension is available
   */
  private async getPythonExtension(): Promise<IExtensionApi | undefined> {

    let extension = vscode.extensions.getExtension(PYTHON_EXTENSION)
    if (!extension) {
      return
    }

    this.logger.debug("Python extension is available")

    if (extension.isActive) {
      this.logger.debug("Python extension is active")
      return extension.exports
    }

    this.logger.debug("Activating python extension")
    return await extension.activate()
  }
}
