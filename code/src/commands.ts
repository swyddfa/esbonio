import * as vscode from "vscode";
import { getOutputLogger } from "./log";

const PYTHON_EXT = "ms-python.python"

export const INSERT_LINK = 'esbonio.insert.link'
export const INSERT_INLINE_LINK = 'esbonio.insert.inlineLink'
export const INSTALL_LANGUAGE_SERVER = 'esbonio.languageServer.install'
export const UPDATE_LANGUAGE_SERVER = 'esbonio.languageServer.update'

function installLanguageServer(): Promise<null> {
  let logger = getOutputLogger()
  let promise: Promise<null> = new Promise((resolve, reject) => {

    getPython().then(python => {
      let process = new vscode.ProcessExecution(python, ["-m", "pip", "install", "esbonio[lsp]"])
      let task = new vscode.Task({ type: 'process' }, vscode.TaskScope.Workspace, 'Install Language Server', 'esbonio', process)

      // Executing a one-shot task and waiting for it to finish seems a little awkward?
      vscode.tasks.executeTask(task).then(texec => {
        let listener: vscode.Disposable
        listener = vscode.tasks.onDidEndTask(end => {
          if (texec === end.execution) {
            logger.debug("Installation task has completed.")
            listener.dispose()
            resolve(null)
          }
        })
      }, err => reject(err))
    }).catch(err => reject(err))
  })

  return promise
}

function updateLanguageServer(): Promise<null> {
  let logger = getOutputLogger()
  let promise: Promise<null> = new Promise((resolve, reject) => {

    getPython().then(python => {
      let process = new vscode.ProcessExecution(python, ["-m", "pip", "install", "--upgrade", "esbonio[lsp]"])
      let task = new vscode.Task({ type: 'process' }, vscode.TaskScope.Workspace, 'Update Language Server', 'esbonio', process)

      // Executing a one-shot task and waiting for it to finish seems a little awkward?
      vscode.tasks.executeTask(task).then(texec => {
        let listener: vscode.Disposable
        listener = vscode.tasks.onDidEndTask(end => {
          if (texec === end.execution) {
            logger.debug("Update task has completed.")
            listener.dispose()
            resolve(null)
          }
        })
      }, err => reject(err))
    }).catch(err => reject(err))
  })

  return promise
}

/**
 * Get the path to the right Python environment to use.
 *
 * - If the user has set a value for `esbonio.pythonPath` use that.
 * - Otherwise, if the official Python extension is available this function will attempt
 *   to retrieve the Python
 */
export function getPython(): Promise<string> {
  let logger = getOutputLogger()
  let python = vscode.workspace.getConfiguration('esbonio').get<string>('pythonPath')

  // If the user has set a value, use that.
  //
  // TODO: Implement variable expansions like ${workspaceRoot}, ${config:xxx} etc.
  //       Ideally it would be something VSCode could do for us, but as far as I can
  //       tell it's not available yet
  //       https://github.com/microsoft/vscode/issues/46471
  if (python) {
    logger.debug(`Using user configured Python: ${python}`)
    return Promise.resolve(python)
  }

  // If the  python extension's `python.pythonPath` is available, let's use that.
  return getPythonExtPython()

  // TODO: If the above fails, or the Python extension is not available, implement a
  //       fallback that attempts to discover the system Python?
}

function getPythonExtPython(): Promise<string> {
  let logger = getOutputLogger()
  return new Promise((resolve, reject) => {
    let root = vscode.workspace.workspaceFolders[0]
    let options = {
      workspaceFolder: root.uri.path
    }

    getPythonExtension().then(_ => {
      vscode.commands.executeCommand<string>("python.interpreterPath", options).then(python => {
        logger.debug(`Using python from the python extension: ${python}`)
        resolve(python)
      }, err => reject(err))
    }).catch(err => reject(err))
  })
}

function getPythonExtension(): Promise<vscode.Extension<any>> {
  let logger = getOutputLogger()
  let pythonExt = vscode.extensions.getExtension(PYTHON_EXT)
  if (!pythonExt) {
    return Promise.reject("The Python extension is not available.")
  }

  if (pythonExt.isActive) {
    return Promise.resolve(pythonExt)
  }

  return new Promise((resolve, reject) => {
    logger.debug("Python extension is available but not yet active, activating...")
    pythonExt.activate().then(ext => resolve(ext), err => reject(err))
  })
}

/**
 * Insert inline link.
 *
 */
async function insertInlineLink(editor: vscode.TextEditor) {

  let link = await getLinkComponents(editor)
  let selection = editor.selection

  let inlineLink = `\`${link.text} <${link.url}>\`_`

  await editor.edit(edit => {
    edit.replace(selection, inlineLink)
  })

  // Clear the selection.
  let position = editor.selection.end
  editor.selection = new vscode.Selection(position, position)
}

/**
 * Insert a link.
 */
async function insertLink(editor: vscode.TextEditor) {

  let link = await getLinkComponents(editor)
  let selection = editor.selection

  let linkRef = `\`${link.text}\`_`
  let linkDef = `.. _${link.text}: ${link.url}\n`

  let lastLine = editor.document.lineAt(editor.document.lineCount - 1)

  await editor.edit(edit => {
    edit.replace(selection, linkRef)
    edit.insert(lastLine.range.end, linkDef)
  })

  // Clear the selection.
  let position = editor.selection.end
  editor.selection = new vscode.Selection(position, position)
}

async function getLinkComponents(editor: vscode.TextEditor) {
  let logger = getOutputLogger()
  let text: string;

  let url = await vscode.window.showInputBox({ prompt: "Link URL", placeHolder: "https://..." })

  let selection = editor.selection
  if (selection.isEmpty) {
    text = await vscode.window.showInputBox({ prompt: "Link Text", placeHolder: "Link Text" })
  } else {
    text = editor.document.getText(selection)
  }

  return { text: text, url: url }
}

/**
 * Register all the commands we contribute to VSCode.
 */
export function registerCommands(context: vscode.ExtensionContext) {
  context.subscriptions.push(vscode.commands.registerCommand(INSTALL_LANGUAGE_SERVER, installLanguageServer))
  context.subscriptions.push(vscode.commands.registerCommand(UPDATE_LANGUAGE_SERVER, updateLanguageServer))

  context.subscriptions.push(vscode.commands.registerTextEditorCommand(INSERT_INLINE_LINK, insertInlineLink))
  context.subscriptions.push(vscode.commands.registerTextEditorCommand(INSERT_LINK, insertLink))
}