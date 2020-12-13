import * as assert from "assert";
import { resolve } from "path";
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

suite('Insert Inline Link', () => {

  test('Without selected text', async () => {
    let responses = new Map()
    responses.set("Link Text", "here")
    responses.set("Link URL", "https://github.com")

    let editorCommands = new EditorCommands(new MockInput(responses))

    const document = await vscode.workspace.openTextDocument({ language: 'rst' })
    const editor = await vscode.window.showTextDocument(document)
    await editor.edit(edit => {
      edit.insert(new vscode.Position(0, 0), "You can find more info ")
    })

    await editorCommands.insertInlineLink(editor)
    let doc = editor.document.getText()
    assert.strictEqual(doc, "You can find more info `here <https://github.com>`_")
  })
})
