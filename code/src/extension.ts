import { ExtensionContext, workspace, window } from "vscode";
import { Executable, LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";
import { getPython, registerCommands } from "./commands";
import { bootstrapLanguageServer } from "./languageServer";
import { getOutputLogger } from "./log";

let client: LanguageClient


export function activate(context: ExtensionContext) {

    let logger = getOutputLogger()
    logger.debug("Extension activated.")
    let python = getPython()

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
    }).catch(err => {

        logger.error(err)
        let message = "Unable to start language server.\n" +
            "See output window for more details"
        window.showErrorMessage(message, { title: "Show Output" }).then(opt => {
            if (opt.title === "Show Output") {
                logger.show()
            }
        })
    })

    registerCommands(context)
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined
    }
    return client.stop()
}