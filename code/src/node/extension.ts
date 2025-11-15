import * as vscode from 'vscode'
import { PythonExtension } from '@vscode/python-extension';

import { OutputChannelLogger } from '../common/log'
import { PythonManager } from './python'
import { PreviewManager } from "./preview";
import { EsbonioClient } from './client'
import { SphinxProcessProvider } from "./processTreeView";

let esbonio: EsbonioClient
let logger: OutputChannelLogger

export interface EsbonioExtension {
  client: EsbonioClient
}

export async function activate(context: vscode.ExtensionContext): Promise<EsbonioExtension> {
  let channel = vscode.window.createOutputChannel("Esbonio", "esbonio-log-output")
  let logLevel = vscode.workspace.getConfiguration('esbonio').get<string>('logging.level')

  logger = new OutputChannelLogger(channel, logLevel)
  logger.debug('Extension activated')

  let python = await getPythonExtension()
  let pythonManager = new PythonManager(python, logger, context)
  esbonio = new EsbonioClient(logger, pythonManager, context, channel)

  let previewManager = new PreviewManager(logger, context, esbonio)
  context.subscriptions.push(vscode.window.registerTreeDataProvider(
    'sphinxProcesses', new SphinxProcessProvider(logger, esbonio)
  ));

  let config = vscode.workspace.getConfiguration("esbonio.server")
  if (config.get("enabled")) {
    logger.debug("Starting server from activate()")
    await esbonio.start()
  }

  return { client: esbonio }
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
  logger.debug('Extension deactivated')
  if (!esbonio) {
    return undefined
  }
  return esbonio.stop()
}
