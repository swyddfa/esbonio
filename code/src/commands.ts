import { commands, Disposable, ExtensionContext, ProcessExecution, Task, tasks, TaskScope, Terminal, window, workspace } from "vscode";
import { getOutputLogger } from "./log";

export const INSTALL_LANGUAGE_SERVER = 'esbonio.languageServer.install'
export const UPDATE_LANGUAGE_SERVER = 'esbonio.languageServer.update'
export const RESTART_LANGUAGE_SERVER = 'esbonio.languageServer.restart'

function installLanguageServer(): Promise<null> {
  let python = getPython()
  let logger = getOutputLogger()

  let process = new ProcessExecution(python, ["-m", "pip", "install", "esbonio[lsp]"])
  let task = new Task({ type: 'process' }, TaskScope.Workspace, 'Install Language Server', 'esbonio', process)

  let promise: Promise<null> = new Promise((resolve, reject) => {

    // Executing a one-shot task and waiting for it to finish seems a little awkward?
    tasks.executeTask(task).then(texec => {
      let listener: Disposable
      listener = tasks.onDidEndTask(end => {
        if (texec === end.execution) {
          logger.debug("Installation task has completed.")
          listener.dispose()
          resolve(null)
        }
      })
    })
  })

  return promise
}

function updateLanguageServer(): Promise<null> {
  let python = getPython()
  let logger = getOutputLogger()

  let process = new ProcessExecution(python, ["-m", "pip", "install", "--upgrade", "esbonio[lsp]"])
  let task = new Task({ type: 'process' }, TaskScope.Workspace, 'Update Language Server', 'esbonio', process)
  let promise: Promise<null> = new Promise((resolve, reject) => {

    // Executing a one-shot task and waiting for it to finish seems a little awkward?
    tasks.executeTask(task).then(texec => {
      let listener: Disposable
      listener = tasks.onDidEndTask(end => {
        if (texec === end.execution) {
          logger.debug("Update task has completed.")
          listener.dispose()
          resolve(null)
        }
      })
    })
  })

  return promise
}

function restartLanguageServer() {
  window.showErrorMessage("Not yet implemented")
}


function findOrCreateTerminal(name: string): Terminal {
  let terminal: Terminal
  window.terminals.forEach(term => {
    if (term.name === name) {
      terminal = term
    }
  })

  if (terminal) {
    return terminal
  }

  terminal = window.createTerminal({ name: name })
  return terminal
}


/**
 * Get the path to the right python environment to use.
 * TODO: Add a config option that lets people inherhit this from the python extension
 * if available.
 */
export function getPython(): string {
  let python = workspace.getConfiguration('esbonio.python').get<string>('path')
  return python
}

/**
 * Register all the commands we contribute to VSCode.
 */
export function registerCommands(context: ExtensionContext) {
  context.subscriptions.push(commands.registerCommand(INSTALL_LANGUAGE_SERVER, installLanguageServer))
  context.subscriptions.push(commands.registerCommand(UPDATE_LANGUAGE_SERVER, updateLanguageServer))
  context.subscriptions.push(commands.registerCommand(RESTART_LANGUAGE_SERVER, restartLanguageServer))
}