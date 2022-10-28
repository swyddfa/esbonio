
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  ERROR = 2
}

export abstract class Logger {

  public level: LogLevel

  constructor() {
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

  abstract log(message: string): void

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

export class ConsoleLogger extends Logger {
  log(message: string): void {
    console.log(message)
  }
}
