import * as vscode from "vscode";

import { EditorCommands, VSCodeInput } from "./editor";
import { createOutputLogger, getOutputLogger } from "./log";
import { EsbonioClient } from "./lsp/client";
import { PythonManager } from "./lsp/python";
import { ServerManager } from "./lsp/server";
import { PreviewManager } from "./preview/view";

export const RESTART_LANGUAGE_SERVER = 'esbonio.languageServer.restart'

let esbonio: EsbonioClient

export async function activate(context: vscode.ExtensionContext) {

    let outputChannel = vscode.window.createOutputChannel('Esbonio')
    let logger = createOutputLogger(outputChannel)

    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(configChanged)
    )

    let editorCommands = new EditorCommands(new VSCodeInput())
    editorCommands.register(context)

    let python = new PythonManager(logger)
    let server = new ServerManager(logger, python, context)
    esbonio = new EsbonioClient(logger, python, server, outputChannel, context)

    let preview = new PreviewManager(logger, context, esbonio)

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
