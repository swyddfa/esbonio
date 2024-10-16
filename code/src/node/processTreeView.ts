import * as vscode from 'vscode'
import { Notifications, Events } from "../common/constants";
import { OutputChannelLogger } from '../common/log'

import { AppCreatedNotification, ClientCreatedNotification, ClientDestroyedNotification, ClientErroredNotification, EsbonioClient, SphinxClientConfig, SphinxInfo } from './client';

/**
 * Tree View provider that visualises the Sphinx processes currently
 * managed by the language server.
 */
export class SphinxProcessProvider implements vscode.TreeDataProvider<ProcessTreeNode> {

  private sphinxClients: Map<string, SphinxProcess> = new Map()

  private _onDidChangeTreeData: vscode.EventEmitter<ProcessTreeNode | undefined | null | void> = new vscode.EventEmitter<ProcessTreeNode | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<ProcessTreeNode | undefined | null | void> = this._onDidChangeTreeData.event;

  constructor(private logger: OutputChannelLogger, client: EsbonioClient) {
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

      case 'sphinxProcess':
        let label = 'Starting...'
        let icon: vscode.ThemeIcon | undefined = new vscode.ThemeIcon("sync~spin")
        let client = this.sphinxClients.get(element.id)!
        let tooltip

        if (client.state === 'running') {
          label = `Sphinx v${client.app?.version}`
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
          collapsibleState: vscode.TreeItemCollapsibleState.Expanded
        }

      case 'sphinxBuilder':
        return {
          label: element.name,
          iconPath: new vscode.ThemeIcon('book'),
          tooltip: new vscode.MarkdownString("**Build Directory**\n\n" + element.uri.fsPath),
          contextValue: element.kind,
          collapsibleState: vscode.TreeItemCollapsibleState.Collapsed
        }

      case 'sphinxCommand':
        let cmd: string[] = []
        element.command.forEach(c => cmd.push(`- ${c}`))

        return {
          label: element.command.join(' '),
          iconPath: new vscode.ThemeIcon('console'),
          tooltip: new vscode.MarkdownString(`**Sphinx Command**\n  ${cmd.join('\n  ')}`),
          contextValue: element.kind,
          collapsibleState: vscode.TreeItemCollapsibleState.None
        }

      case 'python':
        let pyCmd: string[] = []
        element.command?.forEach(c => pyCmd.push(`- ${c}`))

        return {
          label: element.command?.join(' '),
          iconPath: vscode.ThemeIcon.File,
          tooltip: new vscode.MarkdownString(`**Python Command**\n  ${pyCmd.join('\n  ')}`),
          resourceUri: vscode.Uri.parse('file:///test.py'),  // Needed to pull in the icon for Python
          contextValue: element.kind,
          collapsibleState: vscode.TreeItemCollapsibleState.None
        }

      case 'directory':
        return {
          resourceUri: element.uri,
          iconPath: vscode.ThemeIcon.Folder,
          contextValue: element.kind,
          collapsibleState: vscode.TreeItemCollapsibleState.Collapsed,
        }

      case 'file':
        return {
          resourceUri: element.uri,
          iconPath: vscode.ThemeIcon.File,
          contextValue: element.kind,
          command: { command: 'vscode.open', title: `Open ${element.name}`, arguments: [element.uri], },
          collapsibleState: vscode.TreeItemCollapsibleState.None
        }
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
  async getChildren(element?: ProcessTreeNode): Promise<ProcessTreeNode[]> {
    const result: ProcessTreeNode[] = []

    if (!element) {
      for (let process of this.sphinxClients.values()) {

        let cwd = process.config.cwd
        let node: ProcessContainerNode = { kind: 'container', name: cwd, path: cwd }
        result.push(node)
      }

      return result
    }

    switch (element.kind) {
      case 'container':
        for (let [id, process] of this.sphinxClients.entries()) {
          if (element.name === process.config.cwd) {
            let node: SphinxProcessNode = { kind: 'sphinxProcess', id: id }
            result.push(node)
          }
        }
        break
      case 'sphinxProcess':
        let client = this.sphinxClients.get(element.id)
        if (!client) {
          break
        }

        let pythonNode: PythonCommandNode = { kind: 'python', command: client.config.pythonCommand }
        result.push(pythonNode)

        let commandNode: SphinxCommandNode = { kind: 'sphinxCommand', command: client.config.buildCommand }
        result.push(commandNode)

        let app = client.app
        if (!app) {
          break
        }

        let builderNode: SphinxBuilderNode = {
          kind: 'sphinxBuilder',
          name: app.builder_name,
          uri: vscode.Uri.file(app.build_dir)
        }
        result.push(builderNode)

        break

      // Check the build dir for any files/directories
      // TODO: Is there a way to insert VSCode's native file tree here?
      //       It would save having to reimplement it ourselves.
      case 'sphinxBuilder':
      case 'directory':
        let items = await vscode.workspace.fs.readDirectory(element.uri)
        for (let [name, type] of items) {
          let node: FileNode | DirNode = {
            kind: type === vscode.FileType.Directory ? 'directory' : 'file',
            name: name,
            uri: vscode.Uri.joinPath(element.uri, name)
          }
          result.push(node)
        }
        break

      // The following node types have no children
      case 'sphinxCommand':
      case 'python':
      case 'file':
    }

    return result
  }

  /**
   * Called when a new SphinxClient has been created.
   *
   * @param params Information about the newly created client.
   */
  private clientCreated(params: ClientCreatedNotification) {
    this.logger.debug(`sphinx/clientCreated: ${JSON.stringify(params.config, undefined, 2)}`)
    this.sphinxClients.set(params.id, new SphinxProcess(params.config))
    this._onDidChangeTreeData.fire()
  }

  /**
   * Called when a new Sphinx application instance has been created.
   *
   * @param params Information about the newly created app.
   */
  private appCreated(params: AppCreatedNotification) {
    this.logger.debug(`sphinx/appCreated: ${JSON.stringify(params.application, undefined, 2)}`)

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

type ProcessTreeNode = ProcessContainerNode | SphinxProcessNode | SphinxBuilderNode | SphinxCommandNode | PythonCommandNode | DirNode | FileNode

/**
 * Represents a Python command
 */
interface PythonCommandNode {
  kind: 'python'
  command: string[] | undefined
}

/**
 * Represents the sphinx process in the tree view
 */
interface SphinxProcessNode {
  kind: 'sphinxProcess'
  id: string
}

/**
 * Represents the builder used by the parent sphinx process.
 */
interface SphinxBuilderNode {
  kind: 'sphinxBuilder'
  name: string
  uri: vscode.Uri
}

/**
 * Represents the build command used by the parent sphinx process.
 */
interface SphinxCommandNode {
  kind: 'sphinxCommand'
  command: string[]
}

/**
 * Represents a container for the sphinx process
 */
interface ProcessContainerNode {
  kind: 'container'
  name: string
  path: string
}

/**
 * Represents a directory
 */
interface DirNode {
  kind: 'directory'
  name: string
  uri: vscode.Uri
}

/**
 * Represents a file node
 */
interface FileNode {
  kind: 'file'
  name: string
  uri: vscode.Uri
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
