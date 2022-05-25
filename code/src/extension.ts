import * as vscode from "vscode";

import { createOutputLogger, getOutputLogger } from "./log";
import { EsbonioClient } from "./lsp/client";
import { PythonManager } from "./lsp/python";
import { ServerManager } from "./lsp/server";
import { StatusManager } from "./lsp/status";
import { PreviewManager } from "./preview/view";

let esbonio: EsbonioClient

export async function activate(context: vscode.ExtensionContext) {

    let outputChannel = vscode.window.createOutputChannel('Esbonio', 'esbonio-log-output')

    let logger = createOutputLogger(outputChannel)
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(configChanged)
    )

    let python = new PythonManager(logger)
    let server = new ServerManager(logger, python, context)
    esbonio = new EsbonioClient(logger, python, server, outputChannel, context)

    let preview = new PreviewManager(logger, context, esbonio)
    let status = new StatusManager(logger, context, esbonio)

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

async function configChanged(event: vscode.ConfigurationChangeEvent) {
    let config = vscode.workspace.getConfiguration('esbonio')

    let logger = getOutputLogger()
    logger.setLevel(config.get<string>('server.logLevel'))
}
