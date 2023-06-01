import * as vscode from 'vscode'

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  ERROR = 2
}

export class OutputChannelLogger {

  public level: LogLevel

  constructor(
    private channel: vscode.OutputChannel,
    logLevel?: string
  ) {

    this.level = LogLevel.ERROR

    if (logLevel) {
      this.setLevel(logLevel)
    }
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
}
