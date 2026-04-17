import * as assert from 'assert';
import * as vscode from 'vscode';
import { State } from 'vscode-languageclient/node';
import { EsbonioExtension } from '../../node/extension';
import { Commands, Events, Notifications } from "../../common/constants";
import { AppCreatedNotification } from 'src/node/client';
import { PreviewFileResult } from 'src/node/preview';

suite('Extension Test Suite', () => {
  let workspace = vscode.workspace.workspaceFolders![0]

  let extension: vscode.Extension<EsbonioExtension | undefined> | undefined
  let esbonio: EsbonioExtension | undefined

  test('activate', async () => { // Extension should activate
    extension = vscode.extensions.getExtension('swyddfa.esbonio')
    assert.ok(extension && extension.isActive)
    assert.ok(extension && extension.exports)

    esbonio = extension.exports
    assert.ok(esbonio.client)
  });

  test('server starts', async () => { // Language server should start
    let promise = new Promise<void>(async (resolve, reject) => {

      if (!esbonio) {
        reject("Extension not activated")
        return
      }

      try {
        await esbonio.client.start()
        assert.ok(esbonio.client.server && esbonio.client.server !== 'starting')
        assert.strictEqual(esbonio.client.server.state, State.Running)

        resolve()
      } catch(err) {
        reject(err)
      }
    })
    return promise
  });

  test('file open', async () => { // Opening a file should create a Sphinx client instance.
    let promise = new Promise<void>((resolve, reject) => {

      if (!esbonio) {
        reject("Extension not activated")
        return
      }

      try {
        assert.ok(esbonio.client.server && esbonio.client.server !== 'starting')
        assert.strictEqual(esbonio.client.server.state, State.Running)
      } catch(err) {
        reject(err)
        return
      }

      esbonio.client.addHandler(Notifications.SPHINX_APP_CREATED, (params: AppCreatedNotification) => {
        try {
          assert.strictEqual(params.application.version, process.env.EXPECTED_SPHINX_VERSION)

          if (process.env.EXPECTED_PYTHON_VERSION) {
            assert.ok(params.application.python.startsWith(process.env.EXPECTED_PYTHON_VERSION))
          }

          resolve()
        } catch (err) {
          reject(err)
        }
      })
    })

    await vscode.workspace.openTextDocument(vscode.Uri.joinPath(workspace.uri, 'index.rst')).then(doc => {
      vscode.window.showTextDocument(doc)
    })

    return promise
  })

  test('preview open', async () => { // Should be able to open preview
    let promise = new Promise<void>(async (resolve, reject) => {
      if (!esbonio) {
        reject("Extension not activated")
        return
      }

      try{
        assert.ok(esbonio.client.server && esbonio.client.server !== 'starting')
        assert.strictEqual(esbonio.client.server.state, State.Running)
      } catch(err) {
        reject(err)
        return
      }

      let previewUri = vscode.Uri.joinPath(workspace.uri, 'index.rst')

      // If everything works as expected, eventually the preview ready event will fire.
      esbonio.preview.addHandler(Events.PREVIEW_READY, async () => {
        try {
          assert.ok(esbonio!.preview.panel)

          let result: PreviewFileResult = await vscode.commands.executeCommand(Commands.PREVIEW_FILE, {uri: `${previewUri}`, show: false})
          assert.ok(result && result.uri)
          // We can only assume that the preview pane is doing the right thing, as it's quite painful to try and do
          // any introspection.
          // However, we can access the uri directly to peek at the contents.
          let response = await fetch(result.uri)
          let content = await response.text()

          assert.ok(content.includes(process.env.EXPECTED_SPHINX_THEME || "ERROR!!ExpectedThemeNotDefined"))
          resolve()
        } catch (err) {
          reject(err)
        }
      })

      await vscode.commands.executeCommand(Commands.OPEN_PREVIEW_TO_SIDE, previewUri)
    })
    return promise
  });
})
