import * as path from 'path';
import * as vscode from 'vscode';

import { TextDocumentFilter } from 'vscode-languageclient';
import { Events, Notifications, Server } from '../common/constants';
import { OutputChannelLogger } from "../common/log";
import {
  AppCreatedNotification,
  ClientCreatedNotification,
  ClientDestroyedNotification,
  ClientErroredNotification,
  EsbonioClient
} from './client';

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
      (params: AppCreatedNotification) => { this.appCreated(params) }
    )

    client.addHandler(
      Notifications.SPHINX_CLIENT_CREATED,
      (params: ClientCreatedNotification) => { this.clientCreated(params) }
    )

    client.addHandler(
      Notifications.SPHINX_CLIENT_ERRORED,
      (params: ClientErroredNotification) => { this.clientErrored(params) }
    )

    client.addHandler(
      Notifications.SPHINX_CLIENT_DESTROYED,
      (params: ClientDestroyedNotification) => { this.clientDestroyed(params) }
    )
  }

  private clientCreated(params: ClientCreatedNotification) {
    this.logger.debug(`${Notifications.SPHINX_CLIENT_CREATED}: ${JSON.stringify(params, undefined, 2)}`)
    let sphinxConfig = params.config

    let config = vscode.workspace.getConfiguration("esbonio.server")
    let documentSelector = config.get<TextDocumentFilter[]>("documentSelector")
    if (!documentSelector || documentSelector.length === 0) {
      documentSelector = Server.DEFAULT_SELECTOR
    }

    let selector: vscode.DocumentFilter[] = []
    let defaultPattern = path.join(sphinxConfig.cwd, "**", "*")
    for (let docSelector of documentSelector) {
      selector.push({
        scheme: docSelector.scheme,
        language: docSelector.language,
        pattern: docSelector.pattern || defaultPattern
      })
    }

    this.setStatusItem(
      params.id,
      "sphinx",
      "Sphinx[starting]",
      {
        selector: selector,
        busy: true,
        detail: sphinxConfig.buildCommand.join(" "),
        severity: vscode.LanguageStatusSeverity.Information
      }
    )
    this.setStatusItem(
      params.id,
      "python",
      "Python",
      {
        selector: selector,
        detail: sphinxConfig.pythonCommand.join(" "),
        command: { title: "Change Interpreter", command: "python.setInterpreter" },
        severity: vscode.LanguageStatusSeverity.Information
      }
    )
  }

  private clientErrored(params: ClientErroredNotification) {
    this.logger.debug(`${Notifications.SPHINX_CLIENT_ERRORED}: ${JSON.stringify(params, undefined, 2)}`)

    this.setStatusItem(
      params.id,
      "sphinx",
      "Sphinx[failed]",
      {
        busy: false,
        detail: params.error,
        severity: vscode.LanguageStatusSeverity.Error
      }
    )
  }

  private clientDestroyed(params: ClientDestroyedNotification) {
    this.logger.debug(`${Notifications.SPHINX_CLIENT_DESTROYED}: ${JSON.stringify(params, undefined, 2)}`)

    for (let [key, item] of this.statusItems.entries()) {
      if (key.startsWith(params.id)) {
        item.dispose()
        this.statusItems.delete(key)
      }
    }
  }

  private appCreated(params: AppCreatedNotification) {
    this.logger.debug(`${Notifications.SPHINX_APP_CREATED}: ${JSON.stringify(params, undefined, 2)}`)
    let sphinx = params.application

    this.setStatusItem(
      params.id,
      "sphinx",
      `Sphinx[${sphinx.builder_name}] v${sphinx.version}`,
      {
        busy: false,
      }
    )
  }

  private serverStop(_params: any) {
    for (let [key, item] of this.statusItems.entries()) {
      item.dispose()
      this.statusItems.delete(key)
    }
  }

  private setStatusItem(
    id: string,
    name: string,
    value: string,
    params?: StatusItemFields,
  ) {
    let key = `${id}-${name.toLocaleLowerCase().replace(' ', '-')}`
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
