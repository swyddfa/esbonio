import * as vscode from "vscode";
import { Executable, LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";
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
    registerCommands(context)

    try {
        let python = await getPython()
        bootstrap = new LanguageServerBootstrap(python, context)

        let version = await bootstrap.ensureLanguageServer()
        if (!version) {
            logger.error("Language Server is not available")
            return
        }
        logger.info(`Starting Language Server v${version}`)

        client = bootstrap.getLanguageClient()
        client.start()

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

    logger.info("Stopping Language Server")
    await client.stop()

    client = bootstrap.getLanguageClient()
    logger.info("Starting Language Server")
    client.start()

    return
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
