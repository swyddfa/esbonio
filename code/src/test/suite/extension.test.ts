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

    esbonio.logger.channel.show()
  });

  test('server starts', async () => { // Language server should start
    if (!esbonio) {
      assert.fail("Extension not activated")
    }

    await esbonio.client.start()
    assert.ok(esbonio.client.server)
    assert.strictEqual(esbonio.client.server.state, State.Running)
  });

  test('file open', async () => { // Opening a file should create a Sphinx client instance.
    let promise = new Promise<void>((resolve, reject) => {
      if (!esbonio) {
        assert.fail("Extension not activated")
      }

      assert.ok(esbonio.client.server)
      assert.strictEqual(esbonio.client.server.state, State.Running)
      esbonio.client.addHandler(Notifications.SPHINX_APP_CREATED, (params: AppCreatedNotification) => {
        try {
          // Because no config has been applied, should be using bundled Sphinx version
          assert.strictEqual(params.application.version, "8.1.3")
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
        assert.fail("Extension not activated")
      }

      assert.ok(esbonio.client.server)
      assert.strictEqual(esbonio.client.server.state, State.Running)

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

          // Default environment so esbonio should be using fallback theme.
          assert.ok(content.includes("alabaster.css"))
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
