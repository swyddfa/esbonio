import * as vscode from 'vscode'
import { OutputChannelLogger } from '../common/log'
import { EsbonioClient } from './client'
import { Commands } from '../common/constants'

interface PreviewFileParams {
  uri: string
  show?: boolean
}

interface PreviewFileResult {
  uri: string
}

export class PreviewManager {
  private panel?: vscode.WebviewPanel

  // Used to break the cache in iframes.
  private count: number = 0

  constructor(
    private logger: OutputChannelLogger,
    private context: vscode.ExtensionContext,
    private client: EsbonioClient
  ) {
    context.subscriptions.push(
      vscode.commands.registerTextEditorCommand(Commands.OPEN_PREVIEW, this.openPreview, this)
    )
    context.subscriptions.push(
      vscode.commands.registerTextEditorCommand(Commands.OPEN_PREVIEW_TO_SIDE, this.openPreviewToSide, this)
    )
  }

  async openPreview(editor: vscode.TextEditor) {
    return await this.previewEditor(editor, vscode.ViewColumn.Active)
  }

  async openPreviewToSide(editor: vscode.TextEditor) {
    return await this.previewEditor(editor, vscode.ViewColumn.Beside)
  }

  private async previewEditor(editor: vscode.TextEditor, placement: vscode.ViewColumn) {
    let srcUri = editor.document.uri
    this.logger.debug(`Previewing: ${srcUri}`)

    let params: PreviewFileParams = {
      uri: `${srcUri}`,
      show: false
    }

    let result: PreviewFileResult | undefined = await vscode.commands.executeCommand(Commands.PREVIEW_FILE, params)
    this.logger.debug(`Result: ${JSON.stringify(result)}`)
    if (!result || !result.uri) {
      return
    }

    await this.reloadPreview(result.uri, placement)
  }

  private async reloadPreview(uri: string, placement: vscode.ViewColumn) {
    let panel = this.getPanel(placement)

    let scriptNonce = getNonce()
    let cssNonce = getNonce()

    this.count += 1

    panel.webview.html = `
<!DOCTYPE html>
<html>

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src 'nonce-${cssNonce}'; script-src 'nonce-${scriptNonce}'; frame-src ${uri}" />

  <style nonce="${cssNonce}">
    body {
      height: 100vh;
      padding: 0;
      margin: 0;
    }

    iframe {
      height: 100%;
      width: 100%;
    }
  </style>
</head>

<body>
  <iframe id="viewer" src=${uri}?r=${this.count}></iframe>
</body>

</html>
`
  }

  private getPanel(placement: vscode.ViewColumn): vscode.WebviewPanel {
    if (this.panel) {
      return this.panel
    }

    this.panel = vscode.window.createWebviewPanel(
      'esbonioPreview',
      'Esbonio Preview',
      placement,
      { enableScripts: true }
    )

    this.panel.onDidDispose(() => {
      this.panel = undefined
    })

    return this.panel
  }
}



// Taken from
// https://github.com/microsoft/vscode-extension-samples/blob/eed9581e43a19424baa81010d072f3473eda4ccb/webview-sample/src/extension.ts
function getNonce() {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
