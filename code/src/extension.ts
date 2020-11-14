import { ExtensionContext } from "vscode";

import { Executable, LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";

let client: LanguageClient

export function activate(context: ExtensionContext) {
    console.log('Launching server.')
    let exe: Executable = {
        command: 'python3',
        args: ['/home/alex/Projects/esbonio/code/dist/test.py']
    }
    let serverOptions: ServerOptions = exe

    let clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'plaintext' }]
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