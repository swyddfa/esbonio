import * as vscode from 'vscode'

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  ERROR = 2
}

export abstract class Logger {
  public level: LogLevel

  constructor(
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

  abstract log(message: string): void
}

/**
 * A logger that writes messages to an output channel.
 */
export class OutputChannelLogger extends Logger {

  constructor(
    private channel: vscode.OutputChannel,
    logLevel?: string
  ) {
    super(logLevel)
  }

  log(message: string): void {
    this.channel.appendLine(`[client] ${message}`)
  }
}

/**
 * A logger that writes messages to the console.
 */
export class ConsoleLogger extends Logger {

  constructor(
    logLevel?: string
  ) {
    super(logLevel)
  }

  log(message: string): void {
    console.log(`[client] ${message}`)
  }
}
