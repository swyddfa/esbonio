import * as assert from "assert";
import { ConsoleLogger } from "../../node/core/log";
import { PythonManager } from "../../node/lsp/python";
import { ServerManager, shouldPromptUpdate, shouldUpdate } from "../../node/lsp/server";
import { State, mockEditorIntegrations } from "../mock";


const logger = new ConsoleLogger()

suite("ServerManager", () => {


  suite('checkPythonVersion()', () => {

    test('it should return the version if it is compatible', async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'active', pythonPath: '/path/to/python' },
        systemCommands: new Map(
          [["/path/to/python", ["3.7.4   ", ""]]]
        ),
      })

      let python = new PythonManager(editor, logger)
      let server = new ServerManager(editor, logger, python, new State())
      let version = await server.checkPythonVersion('3.6.0')

      assert.deepStrictEqual(version, '3.7.4')
    })

    test('it should notify the user if the version is incompatible', async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'active', pythonPath: '/path/to/python' },
        errorMessages: new Map(
          [["Your configured Python version v3.7.4", undefined]]
        ),
        systemCommands: new Map(
          [["/path/to/python", ["3.7.4   ", ""]]]
        ),
      })

      let python = new PythonManager(editor, logger)
      let server = new ServerManager(editor, logger, python, new State())
      let version = await server.checkPythonVersion('3.8.0')

      assert.deepStrictEqual(version, undefined)
    })
  })

  suite("shouldInstall()", () => {
    test('installBehavior = nothing: it should abort the setup', async () => {
      let editor = mockEditorIntegrations({})

      let python = new PythonManager(editor, logger)
      let server = new ServerManager(editor, logger, python, new State())

      let nextAction = await server.shouldInstall('nothing')
      assert.deepStrictEqual(nextAction, 0 /* Abort */)
    })

    test('installBehavior = automatic: it should continue the setup', async () => {
      let editor = mockEditorIntegrations({})

      let python = new PythonManager(editor, logger)
      let server = new ServerManager(editor, logger, python, new State())

      let nextAction = await server.shouldInstall('automatic')
      assert.deepStrictEqual(nextAction, 2 /* Continue */)
    })

    test('installBehavior = prompt(user cancels): it should abort the setup', async () => {
      let editor = mockEditorIntegrations({
        warningMessages: new Map(
          [["The Esbonio Language Server is not installed", undefined]]
        )
      })

      let python = new PythonManager(editor, logger)
      let server = new ServerManager(editor, logger, python, new State())

      let nextAction = await server.shouldInstall('prompt')
      assert.deepStrictEqual(nextAction, 0 /* Abort */)
    })

    test('installBehavior = prompt(user selects no): it should abort the setup', async () => {
      let editor = mockEditorIntegrations({
        warningMessages: new Map(
          [["The Esbonio Language Server is not installed", { title: "No" }]]
        )
      })

      let python = new PythonManager(editor, logger)
      let server = new ServerManager(editor, logger, python, new State())

      let nextAction = await server.shouldInstall('prompt')
      assert.deepStrictEqual(nextAction, 0 /* Abort */)
    })

    test('installBehavior = prompt(user selects yes): it should continue the setup', async () => {
      let editor = mockEditorIntegrations({
        warningMessages: new Map(
          [["The Esbonio Language Server is not installed", { title: "Yes" }]]
        )
      })

      let python = new PythonManager(editor, logger)
      let server = new ServerManager(editor, logger, python, new State())

      let nextAction = await server.shouldInstall('prompt')
      assert.deepStrictEqual(nextAction, 2 /* Continue */)
    })

    test('installBehavior = prompt(user selects switch): it should retry the setup', async () => {
      let editor = mockEditorIntegrations({
        warningMessages: new Map(
          [["The Esbonio Language Server is not installed", { title: "Switch Environments" }]]
        )
      })

      let python = new PythonManager(editor, logger)
      let server = new ServerManager(editor, logger, python, new State())

      let nextAction = await server.shouldInstall('prompt')
      assert.deepStrictEqual(nextAction, 1 /* Continue */)
    })
  })

  suite("shouldUpdate()", () => {
    let cases = [
      { freq: 'daily', today: "2020-01-10", lastUpdate: "2020-01-10", expect: false },
      { freq: 'weekly', today: "2020-01-10", lastUpdate: "2020-01-10", expect: false },
      { freq: 'monthly', today: "2020-01-10", lastUpdate: "2020-01-10", expect: false },

      { freq: 'daily', today: "2020-01-10", lastUpdate: "2020-01-09", expect: true },
      { freq: 'weekly', today: "2020-01-10", lastUpdate: "2020-01-09", expect: false },
      { freq: 'monthly', today: "2020-01-10", lastUpdate: "2020-01-09", expect: false },

      { freq: 'daily', today: "2020-01-10", lastUpdate: "2020-01-03", expect: true },
      { freq: 'weekly', today: "2020-01-10", lastUpdate: "2020-01-03", expect: true },
      { freq: 'monthly', today: "2020-01-10", lastUpdate: "2020-01-03", expect: false },

      { freq: 'daily', today: "2020-01-10", lastUpdate: "2019-12-10", expect: true },
      { freq: 'weekly', today: "2020-01-10", lastUpdate: "2019-12-10", expect: true },
      { freq: 'monthly', today: "2020-01-10", lastUpdate: "2019-12-10", expect: true },
    ]
    cases.forEach(c => {
      test(`${c.freq}: ${c.lastUpdate} -- ${c.today} expecting ${c.expect}`, () => {
        let today = new Date(Date.parse(c.today))
        let lastUpdate = new Date(Date.parse(c.lastUpdate))

        assert.strictEqual(c.expect, shouldUpdate(c.freq, today, lastUpdate))
      })
    })
  })

  suite("shouldPromptUpdate()", () => {
    let cases = [
      { policy: "automatic", currentVersion: "0.4.0", latestVersion: "0.4.1", expect: false },
      { policy: "promptMajor", currentVersion: "0.4.0", latestVersion: "0.4.1", expect: false },
      { policy: "promptAlways", currentVersion: "0.4.0", latestVersion: "0.4.1", expect: true },

      { policy: "automatic", currentVersion: "0.4.0", latestVersion: "0.5.0", expect: false },
      { policy: "promptMajor", currentVersion: "0.4.0", latestVersion: "0.5.0", expect: false },
      { policy: "promptAlways", currentVersion: "0.4.0", latestVersion: "0.5.0", expect: true },

      { policy: "automatic", currentVersion: "0.4.0", latestVersion: "1.0.0", expect: false },
      { policy: "promptMajor", currentVersion: "0.4.0", latestVersion: "1.0.0", expect: true },
      { policy: "promptAlways", currentVersion: "0.4.0", latestVersion: "1.0.0", expect: true },
    ]
    cases.forEach(c => {
      test(`${c.policy}: ${c.currentVersion} -- ${c.latestVersion} expecting: ${c.expect}`, () => {
        assert.strictEqual(c.expect, shouldPromptUpdate(c.policy, c.currentVersion, c.latestVersion))
      })
    })
  })

})
