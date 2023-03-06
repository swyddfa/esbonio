import * as vscode from "vscode";
import { EsbonioClient } from "./lsp/client";
import { Logger } from "./core/log";

let esbonio: EsbonioClient

export async function activate(context: vscode.ExtensionContext) {

  let outputChannel = vscode.window.createOutputChannel('Esbonio', 'esbonio-log-output')
  let logger = new OutputChannelLogger(outputChannel)
  let logLevel = vscode.workspace.getConfiguration('esbonio').get<string>('server.logLevel')
  logger.setLevel(logLevel)
  logger.debug('Extension activated')

  const serverUri = vscode.Uri.joinPath(context.extensionUri, "dist/browser/worker.js")
  esbonio = new EsbonioClient(serverUri, logger, outputChannel)
  try {
    await esbonio.start()
  } catch (err) {
    console.error(err)
  }
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
