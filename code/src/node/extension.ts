// PYTHONPATH="$(pwd)/bundled/libs" python -S -c "import sys;print('\n'.join(sys.path))"
import * as vscode from 'vscode'

import { OutputChannelLogger } from '../common/log'
import { PythonManager } from './python'
import { PreviewManager } from "./preview";
import { EsbonioClient } from './client'
import { StatusManager } from './status';

let esbonio: EsbonioClient
let logger: OutputChannelLogger

export async function activate(context: vscode.ExtensionContext) {
  let channel = vscode.window.createOutputChannel("Esbonio", "esbonio-log-output")
  let logLevel = vscode.workspace.getConfiguration('esbonio').get<string>('server.logLevel')

  logger = new OutputChannelLogger(channel, logLevel)

  let python = new PythonManager(logger)
  esbonio = new EsbonioClient(logger, python, context, channel)

  let previewManager = new PreviewManager(logger, context, esbonio)
  let statusManager = new StatusManager(logger, context, esbonio)

  let config = vscode.workspace.getConfiguration("esbonio.server")
  if (config.get("enabled")) {
    await esbonio.start()
  }
}

export function deactivate(): Thenable<void> | undefined {
  if (!esbonio) {
    return undefined
  }
  return esbonio.stop()
}
