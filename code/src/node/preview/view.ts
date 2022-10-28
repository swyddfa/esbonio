import * as path from 'path';
import * as vscode from 'vscode'

import { Commands } from "../constants";
import { Logger } from "../core/log";
import { EsbonioClient } from "../lsp/client";


/**
 * Class responsible for generating a preview view of the documentation.
 */
export class PreviewManager {

  private htmlPath: string
  private panel: vscode.WebviewPanel

  constructor(
    private logger: Logger,
    context: vscode.ExtensionContext,
    private esbonio: EsbonioClient
  ) {
    context.subscriptions.push(
      vscode.commands.registerTextEditorCommand(Commands.OPEN_PREVIEW, this.openPreview, this)
    )
    context.subscriptions.push(
      vscode.commands.registerTextEditorCommand(Commands.OPEN_PREVIEW_TO_SIDE, this.openPreviewToSide, this)
    )

    vscode.window.onDidChangeActiveTextEditor(this.onDidChangeEditor, this)

    esbonio.onBuildComplete(async (params) => {
      await this.reloadView()
    })
  }

  async openPreview(editor: vscode.TextEditor) {
    return await this.previewEditor(editor, vscode.ViewColumn.Active)
  }

  async openPreviewToSide(editor: vscode.TextEditor) {
    return await this.previewEditor(editor, vscode.ViewColumn.Beside)
  }

  /**
   * Called whenever the user changes their active text editor.
   * Used to switch the preview to match the current source file
   * the user is editing.
   */
  private async onDidChangeEditor(editor: vscode.TextEditor) {
    if (!editor) {
      return
    }

    let htmlPath = await this.getHtmlPath(editor)
    if (!htmlPath) {
      return
    }

    await this.reloadView(htmlPath)
  }

  private async reloadView(htmlPath?: string) {
    if (!this.panel) {
      return
    }

    if (!htmlPath) {
      htmlPath = this.htmlPath
    }

    this.logger.debug(`Previewing ${htmlPath}`)
    this.panel.webview.postMessage({ reload: htmlPath })
    this.htmlPath = htmlPath
  }

  private async previewEditor(editor: vscode.TextEditor, placement: vscode.ViewColumn) {

    let htmlPath = await this.getHtmlPath(editor)
    this.logger.debug(`HTML Path '${htmlPath}'`)
    if (!htmlPath) {
      return
    }

    let result: { port?: number } = await vscode.commands.executeCommand("esbonio.server.preview", { show: false })
    this.logger.debug(`Result is ${JSON.stringify(result)}`)

    if (!result || !result.port) { return }

    if (!this.panel) {
      this.panel = vscode.window.createWebviewPanel(
        'esbonioPreview',
        'Preview',
        placement,
        { enableScripts: true }
      )

      this.panel.webview.html = this.getWebViewHTML(result.port)
    }

    this.panel.onDidDispose(() => {
      this.panel = undefined
    })

    await this.reloadView(htmlPath)
  }

  /**
   * Get the path section of the url required to preview the file associated with the
   * given editor.
   *
   * @param editor
   * @returns
   */
  private async getHtmlPath(editor: vscode.TextEditor): Promise<string | undefined> {
    let config = this.esbonio.sphinxInfo
    if (!config || !config.srcDir || !config.buildDir) {
      return undefined
    }

    let srcDir = config.srcDir
    let buildDir = config.buildDir
    let sourceUri = editor.document.uri

    if (sourceUri.scheme !== 'file' || !sourceUri.fsPath.startsWith(srcDir)) {
      this.logger.debug(`Ignoring ${sourceUri}`)
      return undefined
    }


    let rstPath = sourceUri.fsPath.replace(srcDir, '')
    let htmlPath = rstPath.replace(new RegExp(`\\${path.extname(rstPath)}`), '.html')

    // Check if the file exists.
    let htmlUri = sourceUri.with({ path: path.join(buildDir, htmlPath) })

    try {
      await vscode.workspace.fs.stat(htmlUri)
      return htmlPath
    } catch (err) {

      this.logger.debug(`Ignoring ${sourceUri}: ${JSON.stringify(err, null, 2)}`)
      return undefined
    }
  }

  private getWebViewHTML(port: number) {

    let scriptNonce = getNonce()
    let cssNonce = getNonce()

    return `<!DOCTYPE html>
            <html>

            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <meta http-equiv="Content-Security-Policy"
                    content="default-src 'none'; style-src 'nonce-${cssNonce}'; script-src 'nonce-${scriptNonce}'; frame-src http://localhost:${port}" />

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
              <iframe id="viewer"></iframe>
              <script nonce="${scriptNonce}">
                let count = 0
                let frame = document.getElementById("viewer")

                window.addEventListener('message', event => {

                    const message = event.data; // The JSON data our extension sent
                    if (!message.reload) {
                        return
                    }

                    count += 1
                    const newUrl = "http://localhost:${port}" + message.reload + "?r=" + count

                    frame.src = newUrl
                });
              </script>
            </body>

            </html>`
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
