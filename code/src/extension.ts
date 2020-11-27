import * as vscode from "vscode";
import { Executable, LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";
import { getPython, registerCommands } from "./commands";
import { bootstrapLanguageServer } from "./languageServer";
import { getOutputLogger } from "./log";

let client: LanguageClient

export function activate(context: vscode.ExtensionContext) {

    let logger = getOutputLogger()
    logger.debug("Extension activated.")
    getPython().then(python => {
        bootstrapLanguageServer(python).then(res => {
            if (!res) {
                logger.debug("Unable to bootstrap language server, will not attempt to start")
                return
            }
            let exe: Executable = {
                command: python,
                args: ['-m', 'esbonio']
            }
            let serverOptions: ServerOptions = exe

            let clientOptions: LanguageClientOptions = {
                documentSelector: [{ scheme: 'file', language: 'rst' }]
            }
            client = new LanguageClient('esbonio', 'Esbonio', serverOptions, clientOptions)
            client.start()
        }).catch(err => showError(err))
    }).catch(err => showError(err))

    registerCommands(context)
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

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined
    }
    return client.stop()
}