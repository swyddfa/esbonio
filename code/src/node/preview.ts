import * as vscode from 'vscode'
import { OutputChannelLogger } from '../common/log'
import { EsbonioClient } from './client'
import { Commands, Events, Notifications } from '../common/constants'
import { ShowDocumentParams, Range } from 'vscode-languageclient'

interface PreviewFileParams {
  uri: string
  show?: boolean
}

interface PreviewFileResult {
  uri: string
}

export class PreviewManager {

  private panel?: vscode.WebviewPanel

  /** The uri of the document currently shown in the preview pane */
  private currentUri?: vscode.Uri

  /** If `true`, indicates that we are currently changing the document being previewed */
  private changingDocument = false

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

    client.addHandler(
      "window/showDocument",
      (params: { params: ShowDocumentParams, default: any }) => this.showDocument(params)
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

  private scrollView(editor: vscode.TextEditor) {
    // For some reason, the object representation of the same URI is not stable
    // leading this check to fail in cases where it should pass.
    // Instead, compare the string representation of the uris.
    if (editor.document.uri.toString() !== this.currentUri?.toString()) {
      return
    }

    // More than one range here implies that some regions of code have been folded.
    // Though I doubt it matters too much for this use case?..
    let range = editor.visibleRanges[0]
    this.client.scrollView(editor.document.uri, range.start.line + 1)
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

    if (this.changingDocument) {
      return
    }

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
    if (!result || !result.uri) {
      // Nothing to show.
      panel.webview.postMessage({ 'show': '<nothing>' })
      return
    }

    this.currentUri = editor.document.uri
  }

  private showDocument(req: { params: ShowDocumentParams, default: any }) {
    let params = req.params
    if (!params.external) {
      return this.showInternalDocument(params)
    }

    if (!this.panel) {
      return
    }

    let panel = this.panel
    let uri = vscode.Uri.parse(params.uri)

    // Needed so that previews work in Codespaces
    // see: https://github.com/swyddfa/esbonio/issues/896
    vscode.env.asExternalUri(uri).then(
      extUri => {
        this.logger.debug(`${uri.toString(true)} -> asExternalUri -> ${extUri.toString(true)}`)

        panel.webview.html = this.getWebViewHTML(`${extUri.scheme}://${extUri.authority}`)
        panel.webview.postMessage({ 'show': extUri.toString(true) })
      },
      err => {
        this.logger.error(`Unable to convert uri to an external uri: ${err}`)
      }
    )

  }

  private showInternalDocument(params: ShowDocumentParams) {
    this.changingDocument = true
    this.currentUri = vscode.Uri.parse(params.uri)

    vscode.window.showTextDocument(
      this.currentUri,
      {
        preserveFocus: true,
        // Force document to open in column one, otherwise VSCode may open editor over the
        // preview pane.
        viewColumn: vscode.ViewColumn.One
      }
    ).then(editor => {
      const range = selectionToRange(params.selection)
      if (range) {
        editor.revealRange(range, vscode.TextEditorRevealType.AtTop)
      }
      this.changingDocument = false
    })

    return
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

  private getWebViewHTML(origin: string): string {

    let scriptNonce = getNonce()
    let cssNonce = getNonce()

    return `
<!DOCTYPE html>
<html>

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy"
        content="default-src 'none';
                 style-src 'nonce-${cssNonce}';
                 style-src-attr 'unsafe-inline';
                 script-src 'nonce-${scriptNonce}';
                 frame-src ${origin}/" />

  <style nonce="${cssNonce}">
    * { box-sizing: border-box;}
    :not(progress) { border: none;}

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

    #no-content {
      font-size: 1.2em;
      line-height: 1.5;
      height: 100%;
      overflow-y: auto;
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
  <div id="no-content" style="display: none">
    <h1>No Content Found</h1>
    <p>The Esbonio extension was unable to locate the built version of the document you are trying to preview.
        The most likely explanation for this is that the document is not part of your documentation project.</p>
    <h3>Troubleshooting</h3>
    <p>However, if you are seeing this message for a document you know to be part of your project, please check the following.</p>
    <ul>
        <li>
          You have the correct Python environment configured, either by running the <code>Python: Select Interpreter</code> command,
          or by setting the <code>esbonio.sphinx.pythonCommand</code> configuration option.
        </li>
        <li>
          The Esbonio extension is using the correct <code>sphinx-build</code> command for your project.
          You can override the default command by setting the <code>esbonio.sphinx.buildCommand</code> option
        </li>
        <li>
          Make sure that Esbonio has built your documentation at least once.
        </li>
        <li>
          Check that there are no errors in the Esbonio output log channel.
          You can open this channel by running the <code>Output: Show Output Channels...</code> command and choosing "Esbonio" from the dropdown
        </li>
        <li>
          If there are no messages or obvious errors in the output channel, you can try setting the <code>esbonio.logging.level</code> to
          <code>debug</code> and restarting the server to get more information.
        </li>
    </ul>
    <p>
      You can find more information in Esbonio's <a href="https://docs.esbon.io/en/latest/">documentation</a>.
      If you have tried all of the steps above and are still seeing this message then please
      <a href="https://github.com/swyddfa/esbonio/issues/new?assignees=&labels=bug%2Ctriage&projects=&template=bug_report.yml">open an issue</a>
      - be sure to include any relevant messages from the output channel!
    </p>
  </div>
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
    const noContent = document.getElementById("no-content")
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

        if (message.show === "<nothing>") {
          status.style.display = "none"

          // Only show the "no content" message if there is not a previous page already being shown
          if (!viewer.src) {
            noContent.style.display = "block"
          }
        } else if (message.show) {
          status.style.display = "flex"
          noContent.style.display = "none"
          viewer.src = message.show

          // Persist the url so we can recover if the webview gets hidden.
          vscode.setState({ url: message.show })
        }
      }

      // Control messages coming from the webpage being shown.
      if (event.origin.startsWith("${origin}")) {
        if (message.ready) {
          status.style.display = "none"
          noContent.style.display = "none"
          vscode.postMessage({ ready: true })
        }
      }

    })
</script>

</html>
`
  }
}


function selectionToRange(selection?: Range): vscode.Range | undefined {
  if (!selection) {
    return
  }

  return new vscode.Range(
    new vscode.Position(selection.start.line, selection.start.character),
    new vscode.Position(selection.end.line, selection.end.character),
  )
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
