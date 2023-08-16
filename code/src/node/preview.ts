import * as vscode from 'vscode'
import { OutputChannelLogger } from '../common/log'
import { EsbonioClient } from './client'
import { Commands, Events, Notifications, Server } from '../common/constants'

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
      vscode.window.onDidChangeTextEditorVisibleRanges(params => this.scrollView(params.textEditor))
    )

    // View -> editor sync scrolling implementation
    client.addHandler(
      Notifications.SCROLL_EDITOR,
      (params: { line: number }) => { this.scrollEditor(params) }
    )

    client.addHandler(
      Events.SERVER_START,
      async (_: any) => {
        // Did we previously have a preview open?
        let editor = findEditorFor(this.currentUri)
        if (editor) {
          await this.openPreviewToSide(editor)
        }
      }
    )

    // Destroy the preview pane if the server goes away
    client.addHandler(
      Events.SERVER_STOP,
      (_: any) => {
        // Closing the preview pane will unset this.currentUri
        let uri = this.currentUri
        this.panel?.dispose()
        this.currentUri = uri
      }
    )
  }

  async openPreview(editor: vscode.TextEditor) {
    return await this.previewEditor(editor, vscode.ViewColumn.Active)
  }

  async openPreviewToSide(editor: vscode.TextEditor) {
    return await this.previewEditor(editor, vscode.ViewColumn.Beside)
  }

  private scrollEditor(params: { line: number }) {
    let editor = findEditorFor(this.currentUri)
    if (!editor) {
      return
    }
    // this.logger.debug(`Scrolling: ${JSON.stringify(params)}`)

    let target = new vscode.Range(
      new vscode.Position(Math.max(0, params.line - 2), 0),
      new vscode.Position(params.line + 2, 0)
    )

    editor.revealRange(target, vscode.TextEditorRevealType.AtTop)
  }

  private scrollView(editor: vscode.TextEditor) {
    if (editor.document.uri !== this.currentUri) {
      return
    }

    // More than one range here implies that some regions of code have been folded.
    // Though I doubt it matters too much for this use case?..
    let range = editor.visibleRanges[0]
    this.client.scrollView(range.start.line + 1)
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
    if (this.currentUri === editor.document.uri && this.panel) {
      // There is nothing to do.
      return
    }

    let panel = this.getPanel(placement || vscode.ViewColumn.Beside)
    let params: PreviewFileParams = {
      uri: `${editor.document.uri}`,
      show: false
    }

    let result: PreviewFileResult | undefined = await vscode.commands.executeCommand(Commands.PREVIEW_FILE, params)
    this.logger.debug(`Result: ${JSON.stringify(result)}`)
    if (!result || !result.uri) {
      return
    }

    this.currentUri = editor.document.uri
    panel.webview.postMessage({ 'show': result.uri })
  }

  private getPanel(placement: vscode.ViewColumn): vscode.WebviewPanel {
    if (this.panel) {
      return this.panel
    }

    this.panel = vscode.window.createWebviewPanel(
      'esbonioPreview',
      'Esbonio Preview',
      { preserveFocus: true, viewColumn: placement },
      { enableScripts: true, retainContextWhenHidden: true }
    )

    let scriptNonce = getNonce()
    let cssNonce = getNonce()

    this.panel.webview.html = `
<!DOCTYPE html>
<html>

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src 'nonce-${cssNonce}'; script-src 'nonce-${scriptNonce}'; frame-src http://localhost:*/" />

  <style nonce="${cssNonce}">
    * { box-sizing: border-box; }

    body {
      height: 100vh;
      padding: 0;
      margin: 0;
      overflow: hidden;
    }

    iframe {
      height: 100%;
      width: 100%;
    }

    #status {
      width: 100%;
      position: fixed;
      bottom: 0;
      background: var(--vscode-editor-background);

      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.5rem;
    }

    #progress-bar {
      flex-grow: 1;
    }

    progress {
      width: 100%;
    }
  </style>
</head>

<body>
  <div id="status">
    <p>Loading...</p>
    <div id="progress-bar">
      <progress aria-label="Content loading…"></progress>
    </div>
  </div>
  <iframe id="viewer"></iframe>
</body>

<script nonce="${scriptNonce}">
    const vscode = acquireVsCodeApi()

    const viewer = document.getElementById("viewer")
    const status = document.getElementById("status")

    console.debug(window.location)

    // Restore previous page?
    const previousState = vscode.getState()
    if (previousState && previousState.url) {
      viewer.src = previousState.url
    }

    window.addEventListener("message", (event) => {
      console.debug("[preview]: ", event.origin, event.data)
      let message = event.data

      // Control messages coming from the webview hosting this page
      if (event.origin.startsWith("vscode-webview://")) {
        if (message.show) {
          status.style.display = "flex"
          viewer.src = message.show

          // Persist the url so we can recover if the webview gets hidden.
          vscode.setState({ url: message.show })
        }
      }

      // Control messages coming from the webpage being shown.
      if (event.origin.startsWith("http://localhost:")) {
        if (message.ready) {
          status.style.display = "none"
          vscode.postMessage({ ready: true })
        }
      }

    })
</script>

</html>
`

    // The webview will notify us when the page has finished loading.
    // Which should also mean the websocket connection is up and running.
    // Try and sync up the view to the editor.
    this.panel.webview.onDidReceiveMessage(message => {
      if (!message.ready) {
        return
      }

      let editor = findEditorFor(this.currentUri)
      if (editor) {
        this.scrollView(editor)
      }
    })

    this.panel.onDidDispose(() => {
      this.panel = undefined
      this.currentUri = undefined
    })

    return this.panel
  }
}


/**
 * Return the text editor showing the given uri.
 * @param uri The uri of the document in the editor
 */
function findEditorFor(uri?: vscode.Uri): vscode.TextEditor | undefined {

  if (!uri) {
    return
  }

  for (let editor of vscode.window.visibleTextEditors) {
    if (editor.document.uri === uri) {
      return editor
    }
  }

  return
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
