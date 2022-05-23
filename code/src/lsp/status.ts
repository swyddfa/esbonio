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
  command?: vscode.Command,
  selector?: vscode.DocumentSelector,
  severity?: vscode.LanguageStatusSeverity,
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
    let selector: (string | vscode.DocumentFilter)[] = []

    if (sphinx.buildDir) {
      buildDir = `Build Files - ${renderPath(workspaceRoot, sphinx.buildDir)}`
    }

    if (sphinx.confDir) {
      confDir = `Config - ${renderPath(workspaceRoot, sphinx.confDir)}`
      selector.push({ language: 'python', pattern: `${sphinx.confDir}/conf.py` })
    }

    if (sphinx.builderName) {
      builderName = `Builder - ${sphinx.builderName}`
    }

    if (sphinx.srcDir) {
      srcDir = `Sources - ${renderPath(workspaceRoot, sphinx.srcDir)}`
      selector.push({ language: 'restructuredtext', pattern: `${sphinx.srcDir}/**/*` })
    }

    if (sphinx.version) {
      version = `Sphinx v${sphinx.version}`
    } else if (result.error) {
      version = "Esbonio Server Error"
    }

    this.setStatusItem('Sphinx Version', version, {
      busy: false,
      selector: selector,
      severity: result.error ? vscode.LanguageStatusSeverity.Error : vscode.LanguageStatusSeverity.Information,
      command: {
        title: 'Restart Server',
        tooltip: "Restart the language server",
        command: Commands.RESTART_SERVER
      }
    })
    this.setStatusItem('Builder', builderName, {
      busy: false,
      selector: selector,
      command: {
        title: "Set Build Command",
        tooltip: "Set the sphinx-build cli options to use",
        command: Commands.SET_BUILD_COMMAND
      }
    })
    this.setStatusItem('Config', confDir, {
      selector: selector,
      command: {
        title: "Select Conf Dir",
        tooltip: "Select a new config directory",
        command: Commands.SELECT_CONFDIR
      }
    })
    this.setStatusItem('Sources', srcDir, {
      selector: selector,
      command: {
        title: "Select Src Dir",
        tooltip: "Select a new sources directory",
        command: Commands.SELECT_SRCDIR
      }
    })
    this.setStatusItem("Build Files", buildDir, {
      selector: selector,
      command: {
        title: "Select Build Dir",
        tooltip: "Select a new build directory",
        command: Commands.SELECT_BUILDDIR
      }
    })
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
    }

    statusItem.text = value

    if (params && params.severity >= 0) {
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
