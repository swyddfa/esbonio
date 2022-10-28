/**
 * In order to make the extension easy to test, it's necessary to enforce
 * a hard divide between the logic of the extension and any code that interacts
 * with the vscode api.
 *
 * The interfaces in this represent that divide.
 */
export interface EditorIntegrations {

  executeEditorCommand(commandId: string, ...args: any[]): Promise<any>

  executeTask(name: string, program: string, args: string[]): Promise<void>

  // Not provided by VSCode, but still useful to be able to mock it out.
  executeSystemCommand(program: string, args: string[]): Promise<CommandOutput>

  getConfiguration(section: string): Configuration | undefined

  getExtension(extensionId: string): any

  getWorkspaceFolders(): WorkspaceFolder[] | undefined

  showErrorMessage(message: string, ...items: any[]): Promise<any | undefined>

  showInformationMessage(message: string, ...items: any[]): Promise<any | undefined>

  showInputBox(options: { value: string, placeHolder: string, prompt: string }): Promise<string>

  showWarningMessage(message: string, ...items: any[]): Promise<any | undefined>

  writeTextToClipboard(text: string): Promise<void>
}

/**
 * Represents output from a command.
 */
export interface CommandOutput {
  stdout: string,
  stderr: string
}


export interface Configuration {
  get<T>(section: string): T | undefined
  update(key: string, value: any)
}

export interface OutputChannel {
  show(): void
}

export interface WorkspaceFolder {
  uri: string
  fsPath: string
}

export interface WorkspaceState {

  workspaceStorage: string

  get<T>(key: string): T
  get<T>(key: string, defaultValue: T): T
  update(key: string, value: any): Promise<void>
}
