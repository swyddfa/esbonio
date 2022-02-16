import * as vscode from "vscode";

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  ERROR = 2
}

let channelLogger: OutputChannelLogger

export abstract class Logger {
  constructor(public level: LogLevel) { }

  abstract log(message: string): void

  info(message: string): void {
    if (this.level <= LogLevel.INFO) {
      this.log(`[INFO ] ${message}`)
    }
  }

  debug(message: string): void {
    if (this.level <= LogLevel.DEBUG) {
      this.log(`[DEBUG] ${message}`)
    }
  }

  error(message: string): void {
    if (this.level <= LogLevel.ERROR) {
      this.log(`[ERROR] ${message}`)
    }
  }
}

class OutputChannelLogger extends Logger {

  constructor(private channel: vscode.OutputChannel, level: LogLevel) {
    super(level)
  }

  log(message: string): void {
    this.channel.appendLine(message)
  }

  show() {
    this.channel.show()
  }
}

/**
 * Return the logger that logs to the output window.
 */
export function getOutputLogger(channel: vscode.OutputChannel) {
  if (!channelLogger) {
    let logLevel: LogLevel

    let level = vscode.workspace.getConfiguration('esbonio').get<string>('server.logLevel')
    switch (level) {
      case 'debug':
        logLevel = LogLevel.DEBUG
        break
      case 'info':
        logLevel = LogLevel.INFO
        break
      case 'error':
        logLevel = LogLevel.ERROR
        break
    }

    channelLogger = new OutputChannelLogger(channel, logLevel)
  }

  return channelLogger
}
