import * as vscode from "vscode";
import { LanguageClient, } from "vscode-languageclient/node";

import { getPython, registerCommands } from "./commands";
import { LanguageServerBootstrap } from "./language-server";
import { getOutputLogger } from "./log";

export const RESTART_LANGUAGE_SERVER = 'esbonio.languageServer.restart'

let bootstrap: LanguageServerBootstrap
let client: LanguageClient

export async function activate(context: vscode.ExtensionContext) {

    let logger = getOutputLogger()
    logger.debug("Extension activated.")

    context.subscriptions.push(vscode.commands.registerCommand(RESTART_LANGUAGE_SERVER, restartLanguageServer))
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(onConfigChanged))
    registerCommands(context)

    try {
        let python = await getPython()
        bootstrap = new LanguageServerBootstrap(python, context)

        if (process.env.VSCODE_DEBUG === "true") {
            client = bootstrap.getTcpClient()
        } else {
            client = await bootstrap.getStdioLanguageClient()
        }

        if (client) {
            client.start()
        }

    } catch (err) {
        showError(err)
    }

}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined
    }
    return client.stop()
}

async function restartLanguageServer(): Promise<null> {
    let logger = getOutputLogger();
    let config = vscode.workspace.getConfiguration('esbonio')

    logger.info("Stopping Language Server")
    await client.stop()

    client = await bootstrap.getStdioLanguageClient()
    logger.info("Starting Language Server")
    client.start()

    // Auto open the output window when debugging to make it easier on developers :)
    if (config.get<string>('server.logLevel') === 'debug') {
        client.outputChannel.show()
    }

    return
}

function onConfigChanged(event: vscode.ConfigurationChangeEvent) {
    let logger = getOutputLogger()
    logger.debug("onConfigChange")

    if (event.affectsConfiguration("esbonio")) {
        vscode.commands.executeCommand(RESTART_LANGUAGE_SERVER)
    }
}

function showError(error) {
    let logger = getOutputLogger()
    logger.error(error)
    let message = "Unable to start language server.\n" +
        "See output window for more details"
    vscode.window.showErrorMessage(message, { title: "Show Output" }).then(opt => {
        if (opt.title === "Show Output") {
            logger.show()
        }
    })
}
