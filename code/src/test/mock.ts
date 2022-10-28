import { PYTHON_EXTENSION } from "../node/constants"
import { CommandOutput, Configuration, EditorIntegrations, WorkspaceFolder, WorkspaceState } from "../node/core/editor"

export interface MockManagerOptions {

  /// Set the result of any command executions.
  commands?: Map<string, any>

  /// Set the result of any system command executions.
  systemCommands?: Map<string, [string, string]>

  /// Set the value of any required config values.
  config?: Map<string, any>

  /// Set the expected error messages and their responses.
  errorMessages?: Map<string, any>

  /// Set the expected info messages and their responses.
  infoMessages?: Map<string, any>

  /// Sets the state of the "python extension"
  python?: MockPythonExtOptions

  /// Set the expected warning messages and their responses.
  warningMessages?: Map<string, any>

  /// Set the list of folders in the workspace.
  workspaces?: WorkspaceFolder[]
}

export interface MockPythonExtOptions {
  status: 'unavailable' | 'inactive' | 'active'
  pythonPath?: string
}

export function mockEditorIntegrations(options: MockManagerOptions): EditorIntegrations {
  return {

    executeEditorCommand(commandId: string, ...args: any[]) {
      if (!options.commands) {
        throw new Error(`No such command: '${commandId}'`)
      }

      if (!options.commands.has(commandId)) {
        throw new Error(`No such command: '${commandId}'`)

      }

      return Promise.resolve(options.commands.get(commandId))
    },

    executeSystemCommand(program: string, args: string[]): Promise<CommandOutput> {
      if (!options.systemCommands || !options.systemCommands.has(program)) {
        throw new Error(`Unexpected command: ${program}`)
      }

      let [stdout, stderr] = options.systemCommands.get(program)
      return Promise.resolve({ stdout, stderr })
    },

    executeTask(name: string, program: string, args: string[]): Promise<void> {
      throw new Error('executeTask: not implemented')
    },

    getExtension(extensionId: string) {
      if (extensionId !== PYTHON_EXTENSION ||
        !options.python ||
        options.python.status === 'unavailable') {
        return undefined
      }

      return getMockPythonExtension(options.python)
    },

    getConfiguration(section: string) {
      if (section !== 'esbonio') {
        throw new Error(`Unsupported config section: '${section}'`)
      }

      return new Config(options.config || new Map())
    },

    getWorkspaceFolders() {
      return options.workspaces || []
    },

    showErrorMessage(message, ...items: any[]) {
      return checkMessage('error', options.errorMessages || new Map(), message, items)
    },

    showInformationMessage(message, ...items: any[]) {
      return checkMessage('information', options.infoMessages || new Map(), message, items)
    },

    showInputBox(options) {
      throw new Error("showInputBox: not implemented")
    },

    showWarningMessage(message, ...items: any[]) {
      return checkMessage('warning', options.warningMessages || new Map(), message, items)
    },

    writeTextToClipboard() {
      throw new Error('writeTextToClipboard: not implemented')
    }
  }
}


function checkMessage(type: string, expectedMessages: Map<string, any>, message, ...items: any[]): Promise<any> {
  if (!expectedMessages) {
    throw new Error(`Unexpected ${type} message: '${message}'`)
  }

  let key: string;

  if (expectedMessages.has(message)) {
    key = message
  } else {
    let keys = [...expectedMessages.keys()].filter(k => message.startsWith(k))
    if (keys.length === 0) {
      throw new Error(`Unexpected ${type} message: '${message}'`)
    }

    if (keys.length > 1) {
      throw new Error(`Ambiguous ${type} messages: ${keys}`)
    }

    key = keys[0]
  }


  return Promise.resolve(expectedMessages.get(key))
}

function getMockPythonExtension(options: MockPythonExtOptions) {
  let exports = {
    settings: {
      getExecutionDetails: () => {
        return {
          execCommand: [options.pythonPath]
        }
      }
    }
  }
  return {
    isActive: options.status === 'active',
    exports,
    activate() {
      return Promise.resolve(exports)
    }
  }
}

export class Config implements Configuration {

  private items: Map<string, any>

  constructor(items?: Map<string, any>) {
    this.items = items || new Map()
  }

  get<T>(key: string): T
  get<T>(key: string, defaultValue: T): T
  get(key: string, defaultValue?: unknown): unknown {

    if (!this.items.has(<string>key)) {
      return defaultValue
    }
    return this.items.get(<string>key)
  }

  update(key: string, value: any): Promise<void> {
    this.items.set(key, value)
    return Promise.resolve(null)
  }
}


export class State implements WorkspaceState {

  private items: Map<string, any>
  workspaceStorage: string

  constructor(items?: Map<string, any>) {
    this.items = items || new Map()
    this.workspaceStorage = '/some/path/to/workspace/storage'
  }

  get<T>(key: string): T
  get<T>(key: string, defaultValue: T): T
  get(key: string, defaultValue?: unknown): unknown {

    if (!this.items.has(<string>key)) {
      return defaultValue
    }
    return this.items.get(<string>key)
  }

  update(key: string, value: any): Promise<void> {
    this.items.set(key, value)
    return Promise.resolve(null)
  }
}
