import * as assert from 'assert';
import * as vscode from 'vscode';
import { State } from 'vscode-languageclient/node';
import { EsbonioExtension } from '../../node/extension';

suite('Extension Test Suite', () => {
  // Test that the extension activates and the language server process starts as expected
  test('activate', async () => {
    let ext: vscode.Extension<EsbonioExtension | undefined> | undefined = vscode.extensions.getExtension('swyddfa.esbonio')
    assert.ok(ext && ext.isActive)
    assert.ok(ext && ext.exports)

    let {client}: EsbonioExtension = ext.exports
    assert.ok(client.server)
    assert.equal(client.server.state, State.Running)
  });
});
