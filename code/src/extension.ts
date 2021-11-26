import * as vscode from "vscode";

import { EditorCommands, VSCodeInput } from "./editor";
import { getOutputLogger } from "./log";
import { EsbonioClient } from "./lsp/client";
import { PythonManager } from "./lsp/python";
import { ServerManager } from "./lsp/server";
import { PreviewManager } from "./preview/view";

export const RESTART_LANGUAGE_SERVER = 'esbonio.languageServer.restart'

let esbonio: EsbonioClient

export async function activate(context: vscode.ExtensionContext) {

    let logger = getOutputLogger()
    logger.debug("Extension activated.")

    let editorCommands = new EditorCommands(new VSCodeInput())
    editorCommands.register(context)

    let python = new PythonManager(logger)
    let server = new ServerManager(logger, python, context)
    esbonio = new EsbonioClient(logger, python, server, context)

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
