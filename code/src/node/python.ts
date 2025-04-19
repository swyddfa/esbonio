import * as vscode from 'vscode'
import { PythonExtension } from '@vscode/python-extension';

import { OutputChannelLogger } from "../common/log";
import { Events } from '../common/constants';


export class PythonManager {
  private handlers: Map<string, any[]>

  constructor(
    private python: PythonExtension | undefined,
    private logger: OutputChannelLogger,
    context: vscode.ExtensionContext
  ) {
    this.handlers = new Map()

    if (python) {
      context.subscriptions.push(
        python.environments.onDidChangeActiveEnvironmentPath((event) => {
          logger.debug(`Changed active Python env: ${JSON.stringify(event, undefined, 2)}`)
          this.callHandlers(Events.PYTHON_ENV_CHANGE, event)
        })
      )
    }
  }

  /**
   * Get the Python command to use.
   *
   * In order of priority:
   * 1. `ESBONIO_SERVER_PYCMD` environment variable
   * 2. User configured Python path
   * 3. Active Python environment from the Python extension
   *
   * @param scopeUri Determines the scope to get the Python interperter for when using the Python extension
   * @returns
   */
  async getCmd(scopeUri?: vscode.Uri): Promise<string[] | undefined> {

    if (process.env.ESBONIO_SERVER_PYCMD) {
      return [process.env.ESBONIO_SERVER_PYCMD]
    }

    let userPython = vscode.workspace.getConfiguration("esbonio", scopeUri).get<string>("server.pythonPath")
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

    if (!this.python) {
      return
    }

    let activeEnvPath = this.python.environments.getActiveEnvironmentPath(scopeUri)
    this.logger.debug(`Using environment ${activeEnvPath.id}: ${activeEnvPath.path}`)

    let activeEnv = await this.python.environments.resolveEnvironment(activeEnvPath)
    if (!activeEnv) {
      this.logger.error(`Python extension: Unable to resolve environment '${activeEnvPath.path}'`)
      return
    }

    let pythonUri = activeEnv.executable.uri
    if (!pythonUri) {
      this.logger.error("Python extension: URI of Python executable is undefined...")
      return
    }

    return [pythonUri.fsPath]
  }

  async getDebugerCommand(): Promise<string[]> {
    if (!this.python) {
      return []
    }

    return await this.python.debug.getRemoteLauncherCommand('localhost', 5678, true)
  }

  async getDebugerPath(): Promise<string> {
    if (!this.python) {
      return ''
    }

    let path = await this.python.debug.getDebuggerPackagePath()
    return path || ''
  }

  public addHandler(event: string, handler: any) {
    if (this.handlers.has(event)) {
      this.handlers.get(event)?.push(handler)
    } else {
      this.handlers.set(event, [handler])
    }
  }

  private callHandlers(method: string, params: any) {
    this.handlers.get(method)?.forEach(handler => {
      try {
        handler(params)
      } catch (err) {
        this.logger.error(`Error in '${method}' notification handler: ${err}`)
      }
    })
  }

}
