import { ExtensionContext, workspace, window } from "vscode";

import { Executable, LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";

let client: LanguageClient

/**
 * Given the python interpreter to use, check to see if the language server is present.
 *
 * If it's not, give the user chance to install it. Will return false if we shouldn't
 * attempt to start the language server.
 */
function checkLanguageServer(python: string): Promise<boolean> {
    let promise: Promise<boolean> = new Promise((resolve, reject) => {



        let message = "The Esbonio language server is not installed. Would you like to install it?"
        window.showWarningMessage(message, { title: "Yes" }, { title: "No" }).then(res => {
            if (res && res.title === "Yes") {
                console.log("Installing language server...")

            }
            // Server not installed and user denied the prompt to install.
            // No point in trying to start the server.
            resolve(false)
        })
    })

    return promise
}

export function activate(context: ExtensionContext) {


    let python = workspace.getConfiguration('esbonio.python').get<string>('path')
    console.log("Python path is: " + python)

    checkLanguageServer(python)

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
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined
    }
    return client.stop()
}