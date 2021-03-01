import * as vscode from "vscode";

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  ERROR = 2
}

let channelLogger: OutputChannelLogger

abstract class Logger {
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

export class OutputChannelLogger extends Logger {
  private channel: vscode.OutputChannel

  constructor(name: string, level: LogLevel) {
    super(level)
    this.channel = vscode.window.createOutputChannel(name)
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
export function getOutputLogger() {
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

    channelLogger = new OutputChannelLogger('Esbonio', logLevel)
  }

  return channelLogger
}