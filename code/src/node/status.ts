import * as vscode from 'vscode';
import * as path from 'path';

import { OutputChannelLogger } from "../common/log";
import { EsbonioClient, SphinxInfo } from './client';
import { Events, Notifications } from '../common/constants';

interface StatusItemFields {
  busy?: boolean
  detail?: string,
  command?: vscode.Command,
  selector?: vscode.DocumentSelector,
  severity?: vscode.LanguageStatusSeverity
}

export class StatusManager {

  private statusItems: Map<string, vscode.LanguageStatusItem>

  constructor(
    private logger: OutputChannelLogger,
    private context: vscode.ExtensionContext,
    private client: EsbonioClient,
  ) {
    this.statusItems = new Map()

    client.addHandler(
      Events.SERVER_STOP,
      (params: any) => { this.serverStop(params) }
    )

    client.addHandler(
      Notifications.SPHINX_APP_CREATED,
      (params: SphinxInfo) => { this.createApp(params) }
    )
  }

  private createApp(info: SphinxInfo) {

    let confUri = vscode.Uri.file(info.conf_dir)
    let workspaceFolder = vscode.workspace.getWorkspaceFolder(confUri)
    if (!workspaceFolder) {
      this.logger.error(`Unable to find workspace containing: ${info.conf_dir}`)
      return
    }

    let selector: vscode.DocumentFilter[] = []

    let confPattern = uriToPattern(confUri)
    selector.push({ language: "python", pattern: confPattern })

    let srcUri = vscode.Uri.file(info.src_dir)
    let srcPattern = uriToPattern(srcUri);
    selector.push({ language: 'restructuredtext', pattern: srcPattern })

    let itemId = `${workspaceFolder.uri}`
    let buildUri = vscode.Uri.file(info.build_dir)
    this.setStatusItem(itemId, "sphinx", `Sphinx v${info.version}`, { selector: selector })
    this.setStatusItem(itemId, "builder", `Builder - ${info.builder_name}`, { selector: selector })
    this.setStatusItem(itemId, "srcdir", `Source - ${renderPath(workspaceFolder, srcUri)}`, { selector: selector })
    this.setStatusItem(itemId, "confdir", `Config - ${renderPath(workspaceFolder, confUri)}`, { selector: selector })
    this.setStatusItem(itemId, "builddir", `Build - ${renderPath(workspaceFolder, buildUri)}`, { selector: selector })
  }

  private serverStop(_params: any) {
    for (let [key, item] of this.statusItems.entries()) {
      item.dispose()
      this.statusItems.delete(key)
    }
  }

  private setStatusItem(
    sphinxId: string,
    name: string,
    value: string,
    params?: StatusItemFields,
  ) {
    let key = `${sphinxId}-${name.toLocaleLowerCase().replace(' ', '-')}`
    let statusItem = this.statusItems.get(key)

    if (!statusItem) {
      statusItem = vscode.languages.createLanguageStatusItem(key, { language: "restructuredtext" })
      statusItem.name = name

      this.statusItems.set(key, statusItem)
    }

    statusItem.text = value

    if (params && params.busy !== undefined) {
      statusItem.busy = params.busy
    }

    if (params && params.detail) {
      statusItem.detail = params.detail
    }

    if (params && params.severity && params.severity >= 0) {
      statusItem.severity = params.severity
    }

    if (params && params.command) {
      statusItem.command = params.command
    }

    if (params && params.selector) {
      statusItem.selector = params.selector
    }
  }
}

function renderPath(workspace: vscode.WorkspaceFolder, uri: vscode.Uri): string {
  let workspacePath = workspace.uri.fsPath
  let uriPath = uri.fsPath

  let result = uriPath

  if (uriPath.startsWith(workspacePath)) {
    result = path.join('.', result.replace(workspacePath, ''))
  }

  if (result.length > 50) {
    result = '...' + result.slice(result.length - 47)
  }

  return result
}

function uriToPattern(uri: vscode.Uri) {
  return path.join(uri.fsPath, "**", "*").replace(/\\/g, '/');
}
