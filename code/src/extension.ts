import { ExtensionContext, workspace } from "vscode";

import { Executable, LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";

let client: LanguageClient

export function activate(context: ExtensionContext) {
    let python = workspace.getConfiguration('esbonio.python').get<string>('path')
    console.log("Python path is: " + python)
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