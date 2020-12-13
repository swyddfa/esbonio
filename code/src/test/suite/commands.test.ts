import * as assert from "assert";
import * as vscode from "vscode";
import { after, before, beforeEach } from "mocha";
import { EditorCommands, UserInput } from "../../commands";

/**
 * Class that mocks out the user input part of the vscode API.
 */
class MockInput implements UserInput {

  constructor(public responses: Map<string, string>) { }

  inputBox(label: string, placeholder: string): Thenable<string> {
    if (this.responses.has(label)) {
      return Promise.resolve(this.responses.get(label))
    }

    return Promise.resolve(undefined)
  }
}

/**
 * Open a new document with the given text.
 */
async function editorWithText(text: string): Promise<vscode.TextEditor> {
  const document = await vscode.workspace.openTextDocument({ language: 'rst' })
  const editor = await vscode.window.showTextDocument(document)
  await editor.edit(edit => {
    edit.insert(new vscode.Position(0, 0), text)
  })

  return editor
}

suite('EditorCommands', () => {

  let editor: vscode.TextEditor

  before(async () => {
    const document = await vscode.workspace.openTextDocument({ language: 'rst' })
    editor = await vscode.window.showTextDocument(document)
  })

  beforeEach(async () => {
    await editor.edit(edit => {
      edit.delete(new vscode.Range(new vscode.Position(0, 0), new vscode.Position(editor.document.lineCount, 0)))
    })
  })

  after(async () => {
    await vscode.commands.executeCommand('workbench.action.closeAllEditors')
  })

  test('insertLink - Without selection', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info ")
    })

    let responses = new Map()
    responses.set("Link Text", "here")
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here`_\n\n.. _here: https://github.com\n")
  })

  test('insertLink - Without selection, cancelled url', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info ")
    })

    let responses = new Map()
    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info ")
  })

  test('insertLink - Without selection, cancelled label', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info ")
    })

    let responses = new Map()
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info ")
  })

  test('insertLink - With newline', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info here\n")
    })

    // Select the text we want the command to use as the label.
    editor.selection = new vscode.Selection(new vscode.Position(0, 23), new vscode.Position(0, 28))

    let responses = new Map()
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here`_\n\n.. _here: https://github.com\n")
  })

  test('insertLink - With selection', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info here")
    })

    // Select the text we want the command to use as the label.
    editor.selection = new vscode.Selection(new vscode.Position(0, 23), new vscode.Position(0, 28))

    let responses = new Map()
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here`_\n\n.. _here: https://github.com\n")
  })

  test('insertLink - With selection, cancelled url', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info here")
    })

    // Select the text we want the command to use as the label.
    editor.selection = new vscode.Selection(new vscode.Position(0, 23), new vscode.Position(0, 28))

    let responses = new Map()
    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info here")
  })

  test('insertLink - Multiple', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info here or upstream\n")
    })

    // Select the text we want the command to use as the label.
    editor.selection = new vscode.Selection(new vscode.Position(0, 23), new vscode.Position(0, 27))

    let responses = new Map()
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertLink(editor)

    responses.set("Link URL", "https://pypi.org")
    editor.selection = new vscode.Selection(new vscode.Position(0, 34), new vscode.Position(0, 43))
    await editorCommands.insertLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here`_ or `upstream`_\n\n.. _here: https://github.com\n.. _upstream: https://pypi.org\n")
  })

  test('insertInlineLink - Without selection', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info ")
    })

    let responses = new Map()
    responses.set("Link Text", "here")
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here <https://github.com>`_")
  })

  test('insertInlineLink - Without selection, cancelled url', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info ")
    })

    let responses = new Map()
    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info ")
  })

  test('insertInlineLink - Without selection, cancelled label', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info ")
    })

    let responses = new Map()
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info ")
  })

  test('insertInlineLink - With selection', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info here")
    })

    // Select the text we want the command to use as the label.
    editor.selection = new vscode.Selection(new vscode.Position(0, 23), new vscode.Position(0, 28))

    let responses = new Map()
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here <https://github.com>`_")
  })

  test('insertInlineLink - With selection, cancelled url', async () => {
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info here")
    })

    // Select the text we want the command to use as the label.
    editor.selection = new vscode.Selection(new vscode.Position(0, 23), new vscode.Position(0, 28))

    let responses = new Map()

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info here")
  })
})
