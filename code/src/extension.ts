import * as vscode from "vscode";

import { EditorCommands, VSCodeInput } from "./editor";
import { getOutputLogger } from "./log";
import { ClientManager } from "./lsp/client";
import { PythonManager } from "./lsp/python";
import { ServerManager } from "./lsp/server";

export const RESTART_LANGUAGE_SERVER = 'esbonio.languageServer.restart'

let client: ClientManager

export async function activate(context: vscode.ExtensionContext) {

    let logger = getOutputLogger()
    logger.debug("Extension activated.")

    let editorCommands = new EditorCommands(new VSCodeInput())
    editorCommands.register(context)

    let python = new PythonManager(logger)
    let server = new ServerManager(logger, python, context)
    client = new ClientManager(logger, python, server, context)
    await client.start()
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined
    }
    return client.stop()
}
