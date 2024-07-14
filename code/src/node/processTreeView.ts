import * as vscode from 'vscode'
import { Notifications, Events } from "../common/constants";
import { AppCreatedNotification, ClientCreatedNotification, ClientDestroyedNotification, ClientErroredNotification, EsbonioClient, SphinxClientConfig, SphinxInfo } from './client';

/**
 * Tree View provider that visualises the Sphinx processes currently
 * managed by the language server.
 */
export class SphinxProcessProvider implements vscode.TreeDataProvider<ProcessTreeNode> {

  private sphinxClients: Map<string, SphinxProcess> = new Map()

  private _onDidChangeTreeData: vscode.EventEmitter<ProcessTreeNode | undefined | null | void> = new vscode.EventEmitter<ProcessTreeNode | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<ProcessTreeNode | undefined | null | void> = this._onDidChangeTreeData.event;

  constructor(client: EsbonioClient) {
    client.addHandler(
      Notifications.SPHINX_CLIENT_CREATED,
      (params: ClientCreatedNotification) => this.clientCreated(params)
    )

    client.addHandler(
      Notifications.SPHINX_APP_CREATED,
      (params: AppCreatedNotification) => this.appCreated(params)
    )

    client.addHandler(
      Notifications.SPHINX_CLIENT_ERRORED,
      (params: ClientErroredNotification) => this.clientErrored(params)
    )

    client.addHandler(
      Notifications.SPHINX_CLIENT_DESTROYED,
      (params: ClientDestroyedNotification) => this.clientDestroyed(params)
    )

    client.addHandler(
      Events.SERVER_STOP,
      (_: any) => { this.serverStopped() }
    )
  }

  /**
   * Return the UI representation of the given element
   *
   * @param element The tree view element to visualise
   * @returns The UI representation of the given element
   */
  getTreeItem(element: ProcessTreeNode): vscode.TreeItem {

    switch (element.kind) {
      case 'container':
        return { label: element.name, collapsibleState: vscode.TreeItemCollapsibleState.Expanded }

      case 'process':
        let label = 'Starting...'
        let icon: vscode.ThemeIcon | undefined = new vscode.ThemeIcon("sync~spin")
        let client = this.sphinxClients.get(element.id)!
        let tooltip

        if (client.state === 'running') {
          label = `Sphinx ${client.app?.version}`
          icon = undefined

        } else if (client.state === 'errored') {
          label = client.errorMessage || 'Errored'
          icon = new vscode.ThemeIcon("error", new vscode.ThemeColor("list.errorForeground"))
          tooltip = new vscode.MarkdownString("```" + (client.errorDetails || '') + "```")
        }

        return {
          label: label,
          iconPath: icon,
          tooltip: tooltip,
          contextValue: element.kind,
          collapsibleState: vscode.TreeItemCollapsibleState.None
        }

      case 'property':
        return { label: 'Prop', collapsibleState: vscode.TreeItemCollapsibleState.None }
    }

  }

  /**
   * Return the children of the given element.
   *
   * When element is `undefined`, return the top level items in the tree.
   *
   * @param element The element to return children for
   * @returns The given element's children
   */
  getChildren(element?: ProcessTreeNode): Thenable<ProcessTreeNode[]> {
    const result: ProcessTreeNode[] = []

    if (!element) {
      for (let process of this.sphinxClients.values()) {

        let cwd = process.config.cwd
        let node: ProcssContainerNode = { kind: 'container', name: cwd, path: cwd }
        result.push(node)
      }

      return Promise.resolve(result)
    }

    switch (element.kind) {
      case 'container':
        for (let [id, process] of this.sphinxClients.entries()) {
          if (element.name === process.config.cwd) {
            let node: SphinxProcessNode = { kind: 'process', id: id }
            result.push(node)
          }
        }
        break
      case 'process':
      case 'property':
    }

    return Promise.resolve(result)
  }

  /**
   * Called when a new SphinxClient has been created.
   *
   * @param params Information about the newly created client.
   */
  private clientCreated(params: ClientCreatedNotification) {
    this.sphinxClients.set(params.id, new SphinxProcess(params.config))
    this._onDidChangeTreeData.fire()
  }

  /**
   * Called when a new Sphinx application instance has been created.
   *
   * @param params Information about the newly created app.
   */
  private appCreated(params: AppCreatedNotification) {
    const client = this.sphinxClients.get(params.id)
    if (!client) { return }

    client.setApplication(params.application)
    this._onDidChangeTreeData.fire()
  }

  /**
   * Called when a SphinxClient encounters an error.
   *
   * @param params Information about the error.
   */
  private clientErrored(params: ClientErroredNotification) {
    const client = this.sphinxClients.get(params.id)
    if (!client) { return }

    client.setError(params.error, params.detail)
    this._onDidChangeTreeData.fire()
  }

  /**
   * Called when a SphinxClient is destroyed.
   *
   * @param params Information about the event.
   */
  private clientDestroyed(params: ClientDestroyedNotification) {
    this.sphinxClients.delete(params.id)
    this._onDidChangeTreeData.fire()
  }

  /**
   * Called when the language server exits
   */
  private serverStopped() {
    this.sphinxClients.clear()
    this._onDidChangeTreeData.fire()
  }
}

type ProcessTreeNode = ProcssContainerNode | SphinxProcessNode | ProcessPropertyNode

/**
 * Represents a property of the sphinx process
 */
interface ProcessPropertyNode {
  kind: 'property'
}

/**
 * Represents the sphinx process in the tree view
 */
interface SphinxProcessNode {
  kind: 'process'
  id: string
}

/**
 * Represents a container for the sphinx process
 */
interface ProcssContainerNode {
  kind: 'container'
  name: string
  path: string
}

class SphinxProcess {

  /**
   * Indicates the current state of the process.
   */
  public state: 'starting' | 'running' | 'errored'

  /**
   * A short message summarising the error
   */
  public errorMessage: string | undefined

  /**
   * A detailed error message
   */
  public errorDetails: string | undefined

  /**
   * Application info
   */
  public app: SphinxInfo | undefined

  constructor(
    public config: SphinxClientConfig,
  ) {
    this.state = 'starting'
  }

  /**
   * Called when the underlying process encounters an error
   *
   * @param error The error message
   */
  setError(error: string, detail: string) {
    this.state = 'errored'
    this.errorMessage = error
    this.errorDetails = detail
  }

  /**
   * Called when the underlying process encounters an error
   *
   * @param error The error message
   */
  setApplication(app: SphinxInfo) {
    this.state = 'running'
    this.app = app
  }
}
