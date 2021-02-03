import * as vscode from "vscode";
import { getOutputLogger } from "./log";

const PYTHON_EXT = "ms-python.python"

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
  let python = vscode.workspace.getConfiguration('esbonio').get<string>('server.pythonPath')

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
 * Iterface that allows us to mock out various user input commands.
 */
export interface UserInput {
  /**
   * Exposes VSCode `showInputBox` function.
   */
  inputBox(label: string, placeholder: string): Thenable<string | undefined>
}

/**
 * Implementation of UserInput that uses VSCode's APIs
 */
class VSCodeInput implements UserInput {

  inputBox(label: string, placeholder: string): Thenable<string> {
    return vscode.window.showInputBox({ prompt: label, placeHolder: placeholder })
  }

}

/**
 * Get the corresponding end of line sequence for the given enum..
 *
 * Is there a built-in way to get this??
 */
function getEOLSequence(eol: vscode.EndOfLine): string {
  switch (eol) {
    case vscode.EndOfLine.LF:
      return "\n"
    case vscode.EndOfLine.CRLF:
      return "\r\n"
  }
}

/**
 * Class that holds all the text editor commands.
 */
export class EditorCommands {

  public static INSERT_LINK = 'esbonio.insert.link'
  public static INSERT_INLINE_LINK = 'esbonio.insert.inlineLink'

  LINK_PATTERN = /\.\.[ ]_\S+:[ ]\S+\n/

  constructor(public userInput: UserInput) { }

  async insertLink(editor: vscode.TextEditor) {
    let link = await this.getLinkInfo(editor)
    if (!link.url || !link.label) {
      return
    }

    let selection = editor.selection
    let eol = getEOLSequence(editor.document.eol)

    let lastLine = editor.document.lineAt(editor.document.lineCount - 1)
    let lineText = editor.document.getText(lastLine.rangeIncludingLineBreak)

    let prefix = ''
    if (lineText.length === 0) {
      let line = editor.document.lineAt(editor.document.lineCount - 2)
      lineText = editor.document.getText(line.rangeIncludingLineBreak)
    } else {
      prefix = eol
    }

    // If the text at the bottom of the page is not a set of links, insert an
    // extra new line to start a separate block.
    if (!this.LINK_PATTERN.test(lineText)) {
      prefix += eol
    }

    let linkRef = `\`${link.label}\`_`
    let linkDef = `${prefix}.. _${link.label}: ${link.url}${eol}`

    await editor.edit(edit => {
      edit.replace(selection, linkRef)
      edit.insert(lastLine.range.end, linkDef)
    })

    // Clear the selection
    let position = editor.selection.end
    editor.selection = new vscode.Selection(position, position)
  }

  /**
 * Insert inline link.
 *
 */
  async insertInlineLink(editor: vscode.TextEditor) {

    let link = await this.getLinkInfo(editor)
    if (!link.url || !link.label) {
      return
    }

    let selection = editor.selection

    let inlineLink = `\`${link.label} <${link.url}>\`_`

    await editor.edit(edit => {
      edit.replace(selection, inlineLink)
    })

    // Clear the selection.
    let position = editor.selection.end
    editor.selection = new vscode.Selection(position, position)
  }

  /**
   * Register all the commands this class provides
   */
  register(context: vscode.ExtensionContext) {
    context.subscriptions.push(vscode.commands.registerTextEditorCommand(EditorCommands.INSERT_INLINE_LINK, this.insertInlineLink, this))
    context.subscriptions.push(vscode.commands.registerTextEditorCommand(EditorCommands.INSERT_LINK, this.insertLink, this))
  }

  /**
   * Helper function that returns the url to be linked and its label
   */
  private async getLinkInfo(editor: vscode.TextEditor) {
    let label: string;
    let url = await this.userInput.inputBox("Link URL", "https://...")

    let selection = editor.selection
    if (selection.isEmpty) {
      label = await this.userInput.inputBox("Link Text", "Link Text")
    } else {
      label = editor.document.getText(selection)
    }

    return { label: label, url: url }
  }
}


/**
 * Register all the commands we contribute to VSCode.
 */
export function registerCommands(context: vscode.ExtensionContext) {
  context.subscriptions.push(vscode.commands.registerCommand(INSTALL_LANGUAGE_SERVER, installLanguageServer))
  context.subscriptions.push(vscode.commands.registerCommand(UPDATE_LANGUAGE_SERVER, updateLanguageServer))

  let editorCommands = new EditorCommands(new VSCodeInput())
  editorCommands.register(context)
}