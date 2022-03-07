import * as child_process from "child_process";
import * as semver from "semver";
import * as vscode from "vscode";

import { promisify } from "util";

import { PYTHON_EXTENSION } from "../constants";
import { Logger } from "../log";

const execFile = promisify(child_process.execFile)

/**
 * Represents a python command to run.
 */
export interface PythonCommand {
  name?: string,
  args: string[]
}

/**
 * Represents output from a command.
 */
export interface CommandOutput {
  stdout: string,
  stderr: string
}

/**
 * Class responsible for managing all things related to the Python interpreter.
 */
export class PythonManager {

  private pythonExtension
  private checkedExtension = false

  constructor(private logger: Logger) { }

  /**
   * Get the command required to run Python from within the configured environment.
   *
   * - If the user has set a value for `esbonio.server.pythonPath` use that.
   * - Otherwise, if the official Python extension is available ask it which Python
   *   environment to use.
   */
  async getCmd(): Promise<string[] | undefined> {
    let userPython = vscode.workspace.getConfiguration('esbonio').get<string>('server.pythonPath')

    if (userPython) {

      // Support for ${workspaceRoot}/...
      let match = userPython.match(/^\${(\w+)}.*/)
      if (match && match[1] === 'workspaceRoot') {
        let workspaceRoot = ""
        let workspaceFolders = vscode.workspace.workspaceFolders

        if (workspaceFolders) {
          workspaceRoot = workspaceFolders[0].uri.fsPath
        }

        userPython = userPython.replace("${workspaceRoot}", workspaceRoot)
      }

      this.logger.debug(`Using user configured Python: ${userPython}`)
      return [userPython]
    }

    await this.ensurePythonExtension()
    if (this.pythonExtension) {
      return this.pythonExtension.settings.getExecutionDetails().execCommand
    }

    // TODO: Implement a fallback that attempts to find the system python.
  }

  /**
   * Returns true if the user has the Python Extension available.
   */
  async hasPythonExtension(): Promise<boolean> {
    await this.ensurePythonExtension()
    if (this.pythonExtension) {
      return true
    }

    return false
  }

  /**
   * If the Python extension is available, change the active environment.
   */
  async changeEnvironment(): Promise<any> {
    await this.ensurePythonExtension()
    if (this.pythonExtension) {
      return await vscode.commands.executeCommand("python.setInterpreter")
    }

  }

  /**
   * Get the version of the configured Python interpreter.
   */
  async getVersion(): Promise<string | undefined> {

    // The output format of python --version does not seem very stable, especially when you
    // involve Anaconda envs. It's probably safer to build and print the version number
    // ourselves.
    let command: PythonCommand = {
      args: [
        "-c",
        'import sys ; print("{0.major}.{0.minor}.{0.micro}".format(sys.version_info))'
      ]
    }

    let { stdout } = await this.execCommand(command)
    let version = stdout.trim()
    this.logger.info(`Python version '${version}'`)

    // Ensure we extracted a valid version number
    if (!semver.parse(version)) {
      this.logger.error("Unable to parse Python version.")
      return undefined
    }

    return version

  }

  /**
   * Execute a python command and only resolve when its finished.
   *
   * The resolved promise will contain the stdout of the command.
   */
  async execCommand(command: PythonCommand): Promise<CommandOutput> {
    let pythonCmd = await this.getCmd()
    if (!pythonCmd) {
      let message = "Unable to run Python command, no environment configured."
      await vscode.window.showErrorMessage(message, { title: "Close" })
      return
    }

    let fullCommand = [...pythonCmd, ...command.args]
    this.logger.debug(`Running Command: ${fullCommand.join(" ")}`)

    return await execFile(fullCommand[0], fullCommand.slice(1))
  }

  /**
   * Run a Python command and only resolve when it's finished.
   *
   * This does not capture the output.
   */
  async runCommand(command: PythonCommand): Promise<null> {
    let pythonCmd = await this.getCmd()
    if (!pythonCmd) {
      let message = "Unable to run Python command, no environment configured."
      await vscode.window.showErrorMessage(message, { title: "Close" })
      return
    }

    let fullCommand = [...pythonCmd, ...command.args]
    this.logger.debug(`Running Command: ${fullCommand.join(" ")}`)

    let process = new vscode.ProcessExecution(fullCommand[0], fullCommand.slice(1))
    let task = new vscode.Task(
      { type: 'process' }, vscode.TaskScope.Workspace, command.name, 'esbonio', process
    )

    let execution = await vscode.tasks.executeTask(task)
    let taskFinished: Promise<null> = new Promise((resolve, reject) => {

      let listener = vscode.tasks.onDidEndTask(ended => {
        if (execution === ended.execution) {
          this.logger.debug("Task finished.")
          listener.dispose()
          resolve(null)
        }
      })
    })

    return await taskFinished
  }

  /**
 * Ensures that if the Python extension is available
 */
  private async ensurePythonExtension() {

    // No need to repeatedly reload the extension.
    if (this.checkedExtension) {
      return
    }

    let pythonExt = vscode.extensions.getExtension(PYTHON_EXTENSION)
    if (pythonExt) {
      this.logger.debug("Python extension is available")

      if (pythonExt.isActive) {
        this.logger.debug("Python extension is active")
        this.pythonExtension = pythonExt.exports
      } else {
        this.logger.debug("Activating python extension")
        this.pythonExtension = await pythonExt.activate()
      }
    }

    this.checkedExtension = true
  }
}
