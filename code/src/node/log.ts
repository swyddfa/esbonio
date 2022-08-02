import * as vscode from "vscode";

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  ERROR = 2
}

let channelLogger: Logger
export class Logger {

  public level: LogLevel

  constructor(private channel: vscode.OutputChannel) {
    this.level = LogLevel.ERROR
  }

  info(message: string): void {
    if (this.level <= LogLevel.INFO) {
      this.log(message)
    }
  }

  debug(message: string): void {
    if (this.level <= LogLevel.DEBUG) {
      this.log(message)
    }
  }

  error(message: string): void {
    if (this.level <= LogLevel.ERROR) {
      this.log(message)
    }
  }

  log(message: string): void {
    this.channel.appendLine(`[client] ${message}`)
  }

  setLevel(level: string): void {
    let logLevel: LogLevel

    switch (level) {
      case 'debug':
        logLevel = LogLevel.DEBUG
        break
      case 'info':
        logLevel = LogLevel.INFO
        break
      default:
        logLevel = LogLevel.ERROR
        break
    }

    this.level = logLevel
  }

  show() {
    this.channel.show()
  }
}

/**
 * Construct the logger that logs to the output window.
 */
export function createOutputLogger(channel: vscode.OutputChannel): Logger {
  if (!channelLogger) {

    let level = vscode.workspace.getConfiguration('esbonio').get<string>('server.logLevel')

    channelLogger = new Logger(channel)
    channelLogger.setLevel(level)
  }

  return channelLogger
}

/**
 * Return the active logger.
 */
export function getOutputLogger(): Logger {
  return channelLogger
}
