import { join } from "path";

import * as vscode from 'vscode'
import { PythonExtension } from '@vscode/python-extension';

import { Logger } from "../common/log";
import { Events } from '../common/constants';
import { Executable } from 'vscode-languageclient/node';

/**
 * Represents the user's esbonio.server.pythonCommand setting.
 */
type UserPython = string | string[] | {
  command: string[]
  env: any
}

export class PythonManager {
  private handlers: Map<string, any[]>

  constructor(
    private python: PythonExtension | undefined,
    private logger: Logger,
    private context: vscode.ExtensionContext
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
   * 2. User configured Python command
   * 3. Active Python environment from the Python extension
   *
   * @param scopeUri Determines the scope to get the Python interperter for when using the Python extension
   * @returns
   */
  async getServerOptions(scopeUri?: vscode.Uri): Promise<Executable | undefined> {

    if (process.env.ESBONIO_SERVER_PYCMD) {
      return await this.serverOptionsFromEnvironment()
    }

    let userPython = vscode.workspace.getConfiguration("esbonio", scopeUri).get<UserPython>("server.pythonCommand")
    if (userPython) {
      return await this.serverOptionsFromUserPython(userPython)
    }

    return await this.serverOptionsFromPythonExtension(scopeUri)
  }

  /**
   * Pull the python command from the environment variable `ESBONIO_SERVER_PYCMD` and use
   * the default environment.
   * @returns ServerOptions
   */
  private async serverOptionsFromEnvironment(): Promise<Executable> {
      this.logger.debug(`Using Python command from ESBONIO_SERVER_PYCMD`)
      return {
        command: process.env.ESBONIO_SERVER_PYCMD!,
        args: ["-S"],  // Isolates the interpreter from its normal environment.
        options: { env: this.getDefaultEnv() }
      }
  }

  /**
   * Return the ServerOptions constructed from the user's config.
   * @param userPython The user's config
   */
  private async serverOptionsFromUserPython(userPython: UserPython): Promise<Executable> {
    this.logger.debug(`Using Python command from user configuration`)
    if (typeof userPython === 'string') {
      return {
        command: resolveConfVars(userPython),
      }
    }

    if (Array.isArray(userPython)) {
      userPython = userPython.map(cmd => resolveConfVars(cmd))
      return {
        command: userPython[0],
        args: userPython.slice(1),
      }
    }

    let command = userPython.command.map(cmd => resolveConfVars(cmd))
    return {
      command: command[0],
      args: command.slice(1),
      options: { env: {...userPython.env, ...process.env} }
    }
  }

  /**
   * Return the ServerOptions, grabbing an interpreter from the Python extension.
   * @param scopeUri The config scope to interrogate the Python extension
   */
  private async serverOptionsFromPythonExtension(scopeUri?: vscode.Uri): Promise<Executable | undefined> {
    if (!this.python) {
      return
    }

    let activeEnvPath = this.python.environments.getActiveEnvironmentPath(scopeUri)
    this.logger.debug(`Using Python extension environment ${activeEnvPath.id}: ${activeEnvPath.path}`)

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

    return {
      command: pythonUri.fsPath,
      args: ["-S"],  // Isolates the interpreter from its normal environment.
      options: { env: this.getDefaultEnv() }
    }
  }

  /*
   * Get the default environment to use with the server.
   * This prepends the bundled environment to the PYTHONPATH to force the use of the bundled version of esbonio.
   */
  getDefaultEnv() {
    const pathsep = process.platform === 'win32' ? ';' : ':'
    const serverLibs = join(this.context.extensionPath, "bundled", "libs")
    const serverEnv: any = {}

    this.logger.debug("Using bundled server environment")
    Object.keys(process.env).forEach((key) => {
      if (key === 'PYTHONPATH') {
        serverEnv[key] = `${serverLibs}${pathsep}${process.env[key]}`
      } else if (!serverEnv[key]) {
        serverEnv[key] = process.env[key]
      }
    });

    if (!serverEnv.PYTHONPATH) {
      serverEnv.PYTHONPATH = serverLibs
    }

    return serverEnv
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

function resolveConfVars(value: string): string {
  // Support for ${workspaceRoot}/...
  let match = value.match(/^\${(\w+)}/)
  if (match && (match[1] === 'workspaceRoot' || match[1] === 'workspaceFolder')) {
    let workspaceRoot = ""
    let workspaceFolders = vscode.workspace.workspaceFolders

    if (workspaceFolders) {
      workspaceRoot = workspaceFolders[0].uri.fsPath
    }

    return value.replace(match[0], workspaceRoot)
  }

  return value
}
