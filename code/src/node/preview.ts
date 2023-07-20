import * as vscode from 'vscode'
import { OutputChannelLogger } from '../common/log'
import { EsbonioClient } from './client'
import { Commands, Notifications } from '../common/constants'

const COOLDOWN = 1000 // ms

interface PreviewFileParams {
  uri: string
  show?: boolean
}

interface PreviewFileResult {
  uri: string
}

export class PreviewManager {

  private panel?: vscode.WebviewPanel

  // The uri of the document currently shown in the preview pane
  private currentUri?: vscode.Uri

  // If set, indicates that the preview pane is currently in control of the editor.
  private viewInControl?: NodeJS.Timeout

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
    context.subscriptions.push(
      vscode.window.onDidChangeActiveTextEditor(this.onDidChangeEditor, this)
    )
    context.subscriptions.push(
      vscode.window.onDidChangeTextEditorVisibleRanges(params => this.scrollView(params))
    )

    client.addHandler(
      Notifications.SCROLL_EDITOR,
      (params: { line: number }) => { this.scrollEditor(params) }
    )
  }

  async openPreview(editor: vscode.TextEditor) {
    return await this.previewEditor(editor, vscode.ViewColumn.Active)
  }

  async openPreviewToSide(editor: vscode.TextEditor) {
    return await this.previewEditor(editor, vscode.ViewColumn.Beside)
  }

  private scrollEditor(params: { line: number }) {
    for (let editor of vscode.window.visibleTextEditors) {
      if (editor.document.uri === this.currentUri) {
        // this.logger.debug(`Scrolling: ${JSON.stringify(params)}`)

        let target = new vscode.Range(
          new vscode.Position(params.line - 2, 0),
          new vscode.Position(params.line + 2, 0)
        )

        // Don't send `view/scroll` messages for a while to prevent the view and
        // editor from fighting each other for control.
        if (this.viewInControl) {
          clearTimeout(this.viewInControl)
        }
        this.viewInControl = setTimeout(() => {
          this.viewInControl = undefined
          this.logger.debug("viewInControl cooldown ended.")
        }, COOLDOWN)

        editor.revealRange(target, vscode.TextEditorRevealType.AtTop)
        break
      }
    }
  }

  private scrollView(event: vscode.TextEditorVisibleRangesChangeEvent) {
    let editor = event.textEditor
    if (editor.document.uri !== this.currentUri) {
      return
    }

    if (this.viewInControl) {
      return
    }

    // More than one range here implies that some regions of code have been folded.
    // Though I doubt it matters too much for this use case?..
    let range = event.visibleRanges[0]
    this.client.scrollView(range.start.line)
  }

  private async onDidChangeEditor(editor?: vscode.TextEditor) {
    if (!editor || !this.panel) {
      return
    }

    let uri = editor.document.uri
    if (["output"].includes(uri.scheme)) {
      return
    }

    await this.previewEditor(editor)
  }

  private async previewEditor(editor: vscode.TextEditor, placement?: vscode.ViewColumn) {
    this.currentUri = editor.document.uri
    this.logger.debug(`Previewing: ${this.currentUri}`)

    let params: PreviewFileParams = {
      uri: `${this.currentUri}`,
      show: false
    }

    let result: PreviewFileResult | undefined = await vscode.commands.executeCommand(Commands.PREVIEW_FILE, params)
    this.logger.debug(`Result: ${JSON.stringify(result)}`)
    if (!result || !result.uri) {
      return
    }

    await this.reloadPreview(result.uri, placement || vscode.ViewColumn.Beside)
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
