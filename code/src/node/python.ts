import * as vscode from 'vscode'
import { PythonExtension } from '@vscode/python-extension';

import { OutputChannelLogger } from "../common/log";


export class PythonManager {
  constructor(private logger: OutputChannelLogger) { }

  async getCmd(scopeUri?: vscode.Uri): Promise<string[] | undefined> {
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

    let activeEnvPath = python.environments.getActiveEnvironmentPath(scopeUri)
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

  async getDebugerCommand(): Promise<string[]> {
    let python = await this.getPythonExtension()
    if (!python) {
      return []
    }

    return await python.debug.getRemoteLauncherCommand('localhost', 5678, true)
  }

  async getDebugerPath(): Promise<string> {
    let python = await this.getPythonExtension()
    if (!python) {
      return ''
    }

    let path = await python.debug.getDebuggerPackagePath()
    return path || ''
  }
  /**
   * Ensures that if the Python extension is available
   */
  private async getPythonExtension(): Promise<PythonExtension | undefined> {
    try {
      return await PythonExtension.api()
    } catch (err) {
      this.logger.error(`Unable to load python extension: ${err}`)
      return undefined
    }
  }

}
