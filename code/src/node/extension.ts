import * as child_process from "child_process";
import * as vscode from "vscode";

import { promisify } from "util";

import { Commands } from "./constants";
import { EditorIntegrations, WorkspaceState } from "./core/editor";
import { Logger } from "./core/log";
import { EsbonioClient } from "./lsp/client";
import { PythonManager } from "./lsp/python";
import { ServerManager } from "./lsp/server";
import { StatusManager } from "./lsp/status";
import { PreviewManager } from "./preview/view";
import { request, RequestOptions } from "https";

let esbonio: EsbonioClient
let logger: OutputChannelLogger


export async function activate(context: vscode.ExtensionContext) {
  let channel = vscode.window.createOutputChannel('Esbonio', 'esbonio-log-output')
  let logLevel = vscode.workspace.getConfiguration('esbonio').get<string>('server.logLevel')

  logger = new OutputChannelLogger(channel)
  logger.setLevel(logLevel)

  let state = new State(context)
  let python = new PythonManager(editor, logger)
  let server = new ServerManager(editor, logger, python, state)

  esbonio = new EsbonioClient(editor, logger, python, server, channel, state)

  let preview = new PreviewManager(logger, context, esbonio)
  let status = new StatusManager(logger, context, esbonio)

  let config = vscode.workspace.getConfiguration("esbonio.server")
  if (config.get("enabled")) {
    await esbonio.start()
  }

  let subscriptions = [
    vscode.workspace.onDidChangeConfiguration(configChanged),
    vscode.commands.registerCommand(Commands.INSTALL_SERVER, server.installServer, server),
    vscode.commands.registerCommand(Commands.UPDATE_SERVER, server.updateServer, server),
    vscode.commands.registerCommand(Commands.RESTART_SERVER, esbonio.restartServer, esbonio),
    vscode.commands.registerCommand(Commands.COPY_BUILD_COMMAND, esbonio.copyBuildCommand, esbonio),
    vscode.commands.registerCommand(Commands.SET_BUILD_COMMAND, esbonio.setBuildCommand, esbonio),
    vscode.commands.registerCommand(Commands.SELECT_BUILDDIR, selectBuildDir),
    vscode.commands.registerCommand(Commands.SELECT_CONFDIR, selectConfDir),
    vscode.commands.registerCommand(Commands.SELECT_SRCDIR, selectSrcDir),
    vscode.workspace.onDidChangeConfiguration(this.configChanged, this)
  ]
  subscriptions.forEach(subscription => {
    context.subscriptions.push(subscription)
  })

}

export function deactivate(): Thenable<void> | undefined {
  if (!esbonio) {
    return undefined
  }
  return esbonio.stop()
}

class OutputChannelLogger extends Logger {
  constructor(private channel: vscode.OutputChannel) {
    super()
  }

  log(message: string): void {
    this.channel.appendLine(`[client] ${message}`)
  }
}

async function selectBuildDir() {
  return await selectFolder("buildDir")
}


async function selectConfDir() {
  return await selectFolder("confDir")
}


async function selectSrcDir() {
  return await selectFolder("srcDir")
}

async function selectFolder(name: string) {
  let rootUri: vscode.Uri
  let config = vscode.workspace.getConfiguration("esbonio.sphinx")

  let rootFolders = vscode.workspace.workspaceFolders
  if (rootFolders) {
    rootUri = rootFolders[0].uri
  }

  let uri = await vscode.window.showOpenDialog({ canSelectFolders: true, defaultUri: rootUri, canSelectMany: false })
  if (!uri) {
    return
  }

  await config.update(name, uri[0].path, vscode.ConfigurationTarget.Workspace)
}

async function configChanged(event: vscode.ConfigurationChangeEvent) {
  let config = vscode.workspace.getConfiguration('esbonio')

  logger.setLevel(config.get<string>('server.logLevel'))
  logger.debug(`ConfigurationChangeEvent`)

  if (!config.get("server.enabled")) {
    await esbonio.stop()
    return
  }

  let conditions = [
    event.affectsConfiguration("esbonio"),
    !config.get<string>('server.pythonPath') && event.affectsConfiguration("python.pythonPath")
  ]

  if (conditions.some(i => i)) {
    await esbonio.restartServer()
  }
}

const execFile = promisify(child_process.execFile)

// The real implementation of all the integration points
const editor: EditorIntegrations = {

  executeSystemCommand: execFile,
  getConfiguration: vscode.workspace.getConfiguration,

  async executeEditorCommand(commandId: string, ...args: any[]) {
    return await vscode.commands.executeCommand(commandId, ...args)
  },

  executeTask(name: string, program: string, args: string[]) {
    let process = new vscode.ProcessExecution(program, args)
    let task = new vscode.Task(
      { type: 'process' }, vscode.TaskScope.Workspace, name, 'esbonio', process
    )

    return new Promise((resolve, reject) => {
      vscode.tasks.executeTask(task).then(execution => {

        let listener = vscode.tasks.onDidEndTask(ended => {
          if (execution === ended.execution) {
            listener.dispose()
            resolve(null)
          }
        })
      })
    })
  },


  getExtension(extensionId: string) {
    return vscode.extensions.getExtension(extensionId)
  },

  getWorkspaceFolders: () => {
    if (!vscode.workspace.workspaceFolders) {
      return undefined
    }

    return vscode.workspace.workspaceFolders.map(folder => {
      return { fsPath: folder.uri.fsPath, uri: folder.uri.toString() }
    })
  },

  httpGet(options: RequestOptions): Promise<string> {
    return new Promise((resolve, reject) => {
      request(options, (response) => {
        let body = ''

        response.on('data', (chunk) => body += chunk)
        response.on('end', () => {
          resolve(body)
        })

      }).on('error', (err) => {
        reject(err)
      }).end()
    })
  },

  async showErrorMessage(message: string, ...items: any[]) {
    return await vscode.window.showErrorMessage(message, ...items)
  },

  async showInputBox(options) {
    return await vscode.window.showInputBox(options)
  },

  async showInformationMessage(message: string, ...items: any[]) {
    return await vscode.window.showInformationMessage(message, ...items)
  },

  async showWarningMessage(message: string, ...items: any[]) {
    return await vscode.window.showWarningMessage(message, ...items)
  },

  async writeTextToClipboard(text: string) {
    return await vscode.env.clipboard.writeText(text)
  },
}

class State implements WorkspaceState {

  public workspaceStorage: string

  private workspaceState: vscode.Memento


  constructor(context: vscode.ExtensionContext) {
    this.workspaceState = context.workspaceState
    this.workspaceStorage = context.storageUri.path
  }

  get<T>(key: string): T;
  get<T>(key: string, defaultValue: T): T;
  get(key: string, defaultValue?: unknown): any {
    return this.workspaceState.get(key, defaultValue)
  }

  async update(key: string, value: any): Promise<void> {
    await this.workspaceState.update(key, value)
    return Promise.resolve(null)
  }
}
