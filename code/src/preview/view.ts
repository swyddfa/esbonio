import * as jsom from "jsdom";
import * as path from 'path';
import * as vscode from 'vscode'

import { Commands } from "../constants";
import { Logger } from "../log";
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
    this.panel.webview.html = await this.getHtmlContent(htmlPath)
    this.htmlPath = htmlPath
  }

  private async previewEditor(editor: vscode.TextEditor, placement: vscode.ViewColumn) {

    let htmlPath = await this.getHtmlPath(editor)
    if (!htmlPath) {
      return
    }

    // Currently we only support one open editor at a time.
    if (!this.panel) {
      let buildDir = this.esbonio.sphinxConfig.buildDir
      this.panel = vscode.window.createWebviewPanel(
        'esbonioPreview', 'Preview',
        placement,
        {
          enableScripts: true,
          localResourceRoots: [vscode.Uri.file(buildDir)]
        }
      )
    }

    this.panel.onDidDispose(() => {
      this.panel = undefined
    })

    await this.reloadView(htmlPath)
  }

  /**
   * Translate the source *.rst (or other) filepath into the *.html path in the
   * build directory that we want to display.
   *
   * @param sourcePath the path to the source file we wish to preview
   * @param sphinx the SphinxConfig object that tells us where the directories are.
   *
   * @returns the translated path or undefined if the file is not part of
   * the srcDir.
   */
  private async getHtmlPath(editor: vscode.TextEditor): Promise<string | undefined> {

    let sourcePath = editor.document.fileName
    if (!this.esbonio.sphinxConfig) {
      return undefined
    }

    let srcDir = this.esbonio.sphinxConfig.srcDir
    let buildDir = this.esbonio.sphinxConfig.buildDir

    if (!sourcePath.startsWith(srcDir)) {
      this.logger.debug(`Ignoring ${sourcePath}`)
      return undefined
    }

    let rstFile = sourcePath.replace(srcDir, '')
    let htmlFile = rstFile.replace(new RegExp(`\\${path.extname(rstFile)}`), '.html')

    return path.join(buildDir, htmlFile)
  }

  /**
   * Given a path to some HTML content load it and prepare it for display
   * within a webview.
   *
   * This includes translating all css, js, image, etc. urls to be webviewuris
   * so that they get loaded correctly.
   */
  private async getHtmlContent(htmlPath: string): Promise<string> {
    // Since all sphinx generated URLs are relative to the current file (e.g. ../../xxxx)
    // we need to join the urls with the html file's parent dir NOT the sphinx build dir.
    let baseDir = path.dirname(htmlPath)

    let dom = await jsom.JSDOM.fromFile(htmlPath)
    let head = dom.window.document.head
    let body = dom.window.document.body

    // Rewrite the stylesheet paths so that they pass the webview security policies
    let styles = head.querySelectorAll('[rel="stylesheet"]')
    styles.forEach(stylesheet => this.rewriteHrefUrl(stylesheet, baseDir))

    // Rewrite script urls
    let headScripts = head.querySelectorAll('script [src]')
    let bodyScripts = body.querySelectorAll('script [src]')
    headScripts.forEach(script => this.rewriteSrcUrl(script, baseDir))
    bodyScripts.forEach(script => this.rewriteSrcUrl(script, baseDir))

    // Rewrite image urls
    let images = body.querySelectorAll('img')
    images.forEach(image => this.rewriteSrcUrl(image, baseDir))

    return dom.serialize()
  }

  private rewriteSrcUrl(element, baseDir: string) {
    let src = element.getAttribute('src')

    let uri = vscode.Uri.file(path.join(baseDir, src))
    let newSrc = this.panel.webview.asWebviewUri(uri)

    element.setAttribute('src', newSrc)
  }

  private rewriteHrefUrl(element, baseDir: string) {
    let src = element.getAttribute('href')

    let uri = vscode.Uri.file(path.join(baseDir, src))
    let newSrc = this.panel.webview.asWebviewUri(uri)

    element.setAttribute('href', newSrc)
  }
}
