import * as semver from "semver";

import { PYTHON_EXTENSION } from "../constants";
import { CommandOutput, EditorIntegrations } from "../core/editor";
import { Logger } from "../core/log";


/**
 * Represents a python command to run.
 */
export interface PythonCommand {
  name?: string,
  args: string[]
}

/**
 * Class responsible for managing all things related to the Python interpreter.
 */
export class PythonManager {

  private pythonExtension
  private checkedExtension = false

  constructor(
    private editor: EditorIntegrations,
    private logger: Logger
  ) { }

  /**
   * Get the command required to run Python from within the configured environment.
   *
   * - If the user has set a value for `esbonio.server.pythonPath` use that.
   * - Otherwise, if the official Python extension is available ask it which Python
   *   environment to use.
   */
  async getCmd(): Promise<string[] | undefined> {

    let userPython = this.editor.getConfiguration('esbonio').get<string>('server.pythonPath')
    if (userPython) {

      // Support for ${workspaceRoot}/...
      let match = userPython.match(/^\${(\w+)}/)
      if (match && (match[1] === 'workspaceRoot' || match[1] === 'workspaceFolder')) {
        let workspaceRoot = ""
        let workspaceFolders = this.editor.getWorkspaceFolders()

        if (workspaceFolders) {
          workspaceRoot = workspaceFolders[0].fsPath
        }

        userPython = userPython.replace(match[0], workspaceRoot)
      }

      this.logger.debug(`Using user configured Python: ${userPython}`)
      return [userPython]
    }

    let python = await this.getPythonExtension()
    if (python) {
      return python.settings.getExecutionDetails().execCommand
    }

    // TODO: Implement a fallback that attempts to find the system python.
  }

  public async hasPythonExtension(): Promise<boolean> {
    return (await this.getPythonExtension()) !== undefined
  }

  /**
   * If the Python extension is available, change the active environment.
   */
  async selectEnvironment(): Promise<any> {
    let python = await this.getPythonExtension()
    if (python) {
      return await this.editor.executeEditorCommand("python.setInterpreter")
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

    let result = await this.execCommand(command)
    if (!result) {
      return undefined
    }

    let version = result.stdout.trim()
    this.logger.info(`Python version: '${version}'`)

    // Ensure we extracted a valid version number
    if (!semver.parse(version)) {
      this.logger.error(`Unable to parse Python version: '${version}'`)
      return undefined
    }

    return version
  }

  /**
   * Execute a python command and only resolve when its finished.
   *
   * The resolved promise will contain the stdout of the command.
   */
  async execCommand(command: PythonCommand): Promise<CommandOutput | undefined> {
    let pythonCmd = await this.getCmd()
    if (!pythonCmd) {
      let message = "Unable to run Python command, no environment configured."
      await this.editor.showErrorMessage(message, { title: "Close" })

      return undefined
    }

    let fullCommand = [...pythonCmd, ...command.args]
    this.logger.debug(`Running Command: ${fullCommand.join(" ")}`)

    return await this.editor.executeSystemCommand(fullCommand[0], fullCommand.slice(1))
  }

  /**
   * Run a Python command and only resolve when it's finished.
   *
   * This does not capture the output.
   */
  async runCommand(command: PythonCommand): Promise<void> {
    let pythonCmd = await this.getCmd()
    if (!pythonCmd) {
      let message = "Unable to run Python command, no environment configured."
      await this.editor.showErrorMessage(message, { title: "Close" })
      return Promise.resolve(null)
    }

    let fullCommand = [...pythonCmd, ...command.args]
    this.logger.debug(`Running Command: ${fullCommand.join(" ")}`)

    return this.editor.executeTask(command.name, fullCommand[0], fullCommand.slice(1))
  }

  /**
   * Ensures that if the Python extension is available
   */
  private async getPythonExtension(): Promise<any | undefined> {

    // No need to repeatedly reload the extension.
    if (this.pythonExtension) {
      return this.pythonExtension
    }

    if (this.checkedExtension && !this.pythonExtension) {
      return undefined
    }

    let pythonExt = this.editor.getExtension(PYTHON_EXTENSION)
    this.checkedExtension = true

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

    return this.pythonExtension
  }
}
