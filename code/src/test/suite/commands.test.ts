import * as assert from "assert";
import * as vscode from "vscode";
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

suite('Insert Inline Link', () => {

  test('Without selection', async () => {
    let editor = await editorWithText("You can find more info ")

    let responses = new Map()
    responses.set("Link Text", "here")
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here <https://github.com>`_")
  })

  test('Without selection, cancelled url', async () => {
    let editor = await editorWithText("You can find more info ")
    let responses = new Map()

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info ")
  })

  test('Without selection, cancelled label', async () => {
    let editor = await editorWithText("You can find more info ")

    let responses = new Map()
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info ")
  })

  test('With selection', async () => {
    let editor = await editorWithText("You can find more info here")

    // Select the text we want the command to use as the label.
    editor.selection = new vscode.Selection(new vscode.Position(0, 23), new vscode.Position(0, 28))

    let responses = new Map()
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here <https://github.com>`_")
  })

  test('With selection, cancelled url', async () => {
    let editor = await editorWithText("You can find more info here")

    // Select the text we want the command to use as the label.
    editor.selection = new vscode.Selection(new vscode.Position(0, 23), new vscode.Position(0, 28))

    let responses = new Map()

    let editorCommands = new EditorCommands(new MockInput(responses))
    await editorCommands.insertInlineLink(editor)

    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info here")
  })
})
