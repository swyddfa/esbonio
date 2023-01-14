import * as vscode from "vscode";
import { LanguageClientOptions } from "vscode-languageclient";
import { LanguageClient } from "vscode-languageclient/browser";

let client: LanguageClient

export function activate(context: vscode.ExtensionContext) {

  let outputChannel = vscode.window.createOutputChannel('Esbonio')
  outputChannel.appendLine('Extension activated')

  let config = vscode.workspace.getConfiguration('esbonio')

  let statusItem = vscode.languages.createLanguageStatusItem('docutils', { language: 'restructuredtext' })
  context.subscriptions.push(statusItem)
  statusItem.text = "Starting..."
  statusItem.busy = true

  let documentSelector = [
    { scheme: 'vscode-vfs', language: 'restructuredtext' }
  ]

  if (config.get<boolean>('server.enabledInPyFiles')) {
    documentSelector.push(
      { scheme: 'vscode-vfs', language: 'python' }
    )
  }

  const clientOptions: LanguageClientOptions = {
    documentSelector: documentSelector,
    initializationOptions: {
      server: {
        logLevel: config.get<string>('server.logLevel'),
        logFilter: config.get<string[]>('server.logFilter'),
      }
    },
    outputChannel: outputChannel
  }

  const path = vscode.Uri.joinPath(context.extensionUri, "dist/browser/worker.js")
  const worker = new Worker(path.toString())

  client = new LanguageClient("esbonio", "Esbonio", clientOptions, worker)

  client.start().then(() => {
    outputChannel.appendLine(`Server ready.`)

    client.onNotification("esbonio/buildComplete", (params) => {
      console.log(params)
      statusItem.text = `Docutils v${params.docutils.version}`
      statusItem.busy = false
    })
  })

}

export function deactivate(): Thenable<void> | undefined {
  if (!client) {
    return undefined
  }
  return client.stop()
}
