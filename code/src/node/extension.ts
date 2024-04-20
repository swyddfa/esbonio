import * as vscode from 'vscode'
import { PythonExtension } from '@vscode/python-extension';

import { OutputChannelLogger } from '../common/log'
import { PythonManager } from './python'
import { PreviewManager } from "./preview";
import { EsbonioClient } from './client'
import { StatusManager } from './status';

let esbonio: EsbonioClient
let logger: OutputChannelLogger

export async function activate(context: vscode.ExtensionContext) {
  let channel = vscode.window.createOutputChannel("Esbonio", "esbonio-log-output")
  let logLevel = vscode.workspace.getConfiguration('esbonio').get<string>('logging.level')

  logger = new OutputChannelLogger(channel, logLevel)

  let python = await getPythonExtension()
  let pythonManager = new PythonManager(python, logger, context)
  esbonio = new EsbonioClient(logger, pythonManager, context, channel)

  let previewManager = new PreviewManager(logger, context, esbonio)
  let statusManager = new StatusManager(logger, context, esbonio)

  let config = vscode.workspace.getConfiguration("esbonio.server")
  if (config.get("enabled")) {
    await esbonio.start()
  }
}

/**
 * Return the python extension's API, if available.
 */
async function getPythonExtension(): Promise<PythonExtension | undefined> {
  try {
    return await PythonExtension.api()
  } catch (err) {
    logger.error(`Unable to load python extension: ${err}`)
    return undefined
  }
}

export function deactivate(): Thenable<void> | undefined {
  if (!esbonio) {
    return undefined
  }
  return esbonio.stop()
}
