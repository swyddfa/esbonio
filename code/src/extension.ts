import * as vscode from "vscode";
import { join } from "path";
import { Executable, LanguageClient, LanguageClientOptions, ServerOptions } from "vscode-languageclient";
import { getPython, registerCommands } from "./commands";
import { LanguageServerBootstrap } from "./language-server";
import { getOutputLogger } from "./log";

export const RESTART_LANGUAGE_SERVER = 'esbonio.languageServer.restart'

let client: LanguageClient

export async function activate(context: vscode.ExtensionContext) {

    let logger = getOutputLogger()
    logger.debug("Extension activated.")

    context.subscriptions.push(vscode.commands.registerCommand(RESTART_LANGUAGE_SERVER, restartLanguageServer))
    registerCommands(context)

    try {
        let python = await getPython()
        let bootstrap = new LanguageServerBootstrap(python, context)
        let config = vscode.workspace.getConfiguration('esbonio')

        let version = await bootstrap.ensureLanguageServer()
        if (!version) {
            logger.error("Language Server is not available")
            return
        }
        logger.info(`Starting Language Server v${version}`)

        let pythonArgs = [
            '-m', 'esbonio',
            '--cache-dir', join(context.storagePath, 'sphinx'),
            '--log-level', config.get<string>('server.logLevel')
        ]

        if (config.get<boolean>('server.hideSphinxOutput')) {
            pythonArgs.push("--hide-sphinx-output")
        }

        let logFilters = config.get<string[]>("server.logFilter")
        if (logFilters) {
            logFilters.forEach(filterName => {
                pythonArgs.push("--log-filter", filterName)
            })
        }

        let exe: Executable = {
            command: python,
            args: pythonArgs
        }

        logger.debug(`Server start command: ${JSON.stringify(exe)}`)
        let serverOptions: ServerOptions = exe

        let clientOptions: LanguageClientOptions = {
            documentSelector: [
                { scheme: 'file', language: 'rst' },
                { scheme: 'file', language: 'python' }
            ]
        }
        client = new LanguageClient('esbonio', 'Esbonio Language Server', serverOptions, clientOptions)
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

function restartLanguageServer(): Promise<null> {
    let logger = getOutputLogger();

    return new Promise((resolve, reject) => {
        logger.info("Stopping Language Server")
        client.stop().then(_ => {
            logger.info("Starting Language Server")
            client.start()
            resolve(null)
        }).catch(err => reject(err))
    })
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
