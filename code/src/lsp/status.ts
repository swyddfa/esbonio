import * as path from 'path';
import * as vscode from "vscode";
import { Commands } from "../constants";
import { Logger } from "../log";
import { BuildCompleteResult, EsbonioClient } from "./client";


/**
 * Basically vscode.LanguageStatusItem, but with all fields optional.
 */
interface StatusItemFields {
  busy?: boolean,
  severity?: vscode.LanguageStatusSeverity,
  command?: vscode.Command,
}

function renderPath(workspaceRoot: string, value: string): string {
  let result: string = value

  if (workspaceRoot && result.startsWith(workspaceRoot)) {
    result = path.join('./', result.replace(workspaceRoot, ''))
  }

  if (result.length > 50) {
    result = '...' + result.slice(result.length - 47)
  }

  return result
}

/**
 * Class dedicated to managing status items.
 */
export class StatusManager {

  private statusItems: Map<string, vscode.LanguageStatusItem>

  constructor(
    private logger: Logger,
    private context: vscode.ExtensionContext,
    private esbonio: EsbonioClient,
  ) {
    this.statusItems = new Map()
    esbonio.onClientStart(() => this.onClientStart())
    esbonio.onClientError(() => this.onClientError())
    esbonio.onBuildComplete((result: BuildCompleteResult) => this.onBuildComplete(result))
    esbonio.onBuildStart(() => this.onBuildStart())
  }

  onClientStart() {
    this.setStatusItem("Sphinx Version", "$(sync~spin) Starting...", { busy: true })
  }

  onClientError() {
    this.setStatusItem("Sphinx Version", "$(error) Error", {
      severity: vscode.LanguageStatusSeverity.Error
    })
  }
  onBuildStart() {
    this.setStatusItem("Builder", "$(sync~spin) Building...", { busy: true })
  }

  onBuildComplete(result: BuildCompleteResult) {

    let workspaceRoot = ''
    if (vscode.workspace.workspaceFolders) {
      workspaceRoot = vscode.workspace.workspaceFolders[0].uri.fsPath
    }

    let sphinx = result.config.sphinx
    let buildDir = ""
    let builderName = ""
    let confDir = ""
    let srcDir = ""
    let version = ""

    if (sphinx.buildDir) {
      buildDir = `Build Files - ${renderPath(workspaceRoot, sphinx.buildDir)}`
    }

    if (sphinx.confDir) {
      confDir = `Config - ${renderPath(workspaceRoot, sphinx.confDir)}`
    }

    if (sphinx.builderName) {
      builderName = `Builder - ${sphinx.builderName}`
    }

    if (sphinx.srcDir) {
      srcDir = `Sources - ${renderPath(workspaceRoot, sphinx.srcDir)}`
    }

    if (sphinx.version) {
      version = `Sphinx v${sphinx.version}`
    } else if (result.error) {
      version = "Esbonio Server Error"
    }

    this.setStatusItem('Sphinx Version', version, {
      busy: false,
      severity: result.error ? vscode.LanguageStatusSeverity.Error : vscode.LanguageStatusSeverity.Information,
      command: {
        title: 'Restart Server',
        tooltip: "Restart the language server",
        command: Commands.RESTART_SERVER
      }
    })
    this.setStatusItem('Builder', builderName, { busy: false })
    this.setStatusItem('Config', confDir)
    this.setStatusItem('Sources', srcDir)
    this.setStatusItem("Build Files", buildDir)
  }

  setStatusItem(name: string, value: string, params?: StatusItemFields) {
    let key = name.toLocaleLowerCase().replace(' ', '-')
    let statusItem: vscode.LanguageStatusItem

    // Clear the item if there is no value.
    if (!value) {

      if (this.statusItems.has(key)) {
        statusItem = this.statusItems.get(key)
        statusItem.dispose()
        this.statusItems.delete(key)
      }

      return
    }

    if (this.statusItems.has(key)) {
      statusItem = this.statusItems.get(key)
    } else {
      statusItem = vscode.languages.createLanguageStatusItem(key, { language: 'restructuredtext' })
      statusItem.name = name

      this.statusItems.set(key, statusItem)
      // this.context.subscriptions.push(statusItem)
    }

    statusItem.text = value

    if (params && params.severity) {
      statusItem.severity = params.severity
    }

    if (params && params.command) {
      statusItem.command = params.command
    }
  }

}
