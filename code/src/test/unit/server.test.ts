import * as assert from "assert";
import { WorkspaceState } from "../../node/core/editor";
import { ConsoleLogger } from "../../node/core/log";
import { PythonManager } from "../../node/lsp/python";
import { ServerManager, shouldPromptUpdate, shouldUpdate } from "../../node/lsp/server";
import { State, mockEditorIntegrations, MockEditorOptions } from "../mock";


function makeServerManager(editorOptions?: MockEditorOptions, state?: WorkspaceState): ServerManager {
  let logger = new ConsoleLogger()
  let editor = mockEditorIntegrations(editorOptions || {})
  let python = new PythonManager(editor, logger)
  return new ServerManager(editor, logger, python, state || new State())
}


suite("ServerManager", () => {

  suite("updateServer()", () => {
    test('it should upgrade the server with the correct version bound', async () => {

      let state = new State()
      let editorOptions: MockEditorOptions = {
        python: { status: 'active', pythonPath: '/path/to/python' },
        expectedTasks: new Map([
          ['/path/to/python', ['-m', 'pip', 'install', '--upgrade', 'esbonio>=0.15.0']]
        ])
      }

      let expectedDate = "2020-01-01T12:00:00.000Z"
      let today = new Date(Date.parse(expectedDate))

      let server = makeServerManager(editorOptions, state)
      await server.updateServer('0.15.0', today)

      assert.deepStrictEqual(expectedDate, state.get(ServerManager.LAST_UPDATE))
    })
  })

  suite("installServer()", () => {
    test('it should installs the server with the correct version bound', async () => {

      let state = new State()
      let editorOptions: MockEditorOptions = {
        python: { status: 'active', pythonPath: '/path/to/python' },
        expectedTasks: new Map([
          ['/path/to/python', ['-m', 'pip', 'install', 'esbonio>=0.15.0']]
        ])
      }

      let expectedDate = "2020-01-01T12:00:00.000Z"
      let today = new Date(Date.parse(expectedDate))

      let server = makeServerManager(editorOptions, state)
      await server.installServer('0.15.0', today)

      assert.deepStrictEqual(expectedDate, state.get(ServerManager.LAST_UPDATE))
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

  suite('checkPythonVersion()', () => {

    test('it should return the version if it is compatible', async () => {
      let editorOptions: MockEditorOptions = {
        python: { status: 'active', pythonPath: '/path/to/python' },
        systemCommands: new Map([
          [
            '/path/to/python -c import sys ; print("{0.major}.{0.minor}.{0.micro}".format(sys.version_info))',
            ["3.7.4   ", ""]
          ]
        ]),
      }

      let server = makeServerManager(editorOptions)
      let version = await server.checkPythonVersion('3.6.0')

      assert.deepStrictEqual(version, '3.7.4')
    })

    test('it should notify the user if the version is incompatible', async () => {
      let editorOptions: MockEditorOptions = {
        python: { status: 'active', pythonPath: '/path/to/python' },
        errorMessages: new Map(
          [["Your configured Python version v3.7.4", undefined]]
        ),
        systemCommands: new Map([
          [
            '/path/to/python -c import sys ; print("{0.major}.{0.minor}.{0.micro}".format(sys.version_info))',
            ["3.7.4   ", ""]
          ]
        ]),
      }

      let server = makeServerManager(editorOptions)
      let version = await server.checkPythonVersion('3.8.0')

      assert.deepStrictEqual(version, undefined)
    })
  })

  suite("getServerVersion()", () => {
    test('if the server is available, it should just return the version', async () => {
      let editorOptions: MockEditorOptions = {
        python: { status: 'active', pythonPath: '/path/to/python' },
        systemCommands: new Map([
          ['/path/to/python -m esbonio --version', ['v0.5.0', '']]
        ])
      }

      let server = makeServerManager(editorOptions)
      let version = await server.getServerVersion('0.15.0', new Date(Date.now()))

      assert.deepStrictEqual('0.5.0', version)
    })

    test('if the server is not available and installBehavior = nothing it should do nothing', async () => {
      let editorOptions: MockEditorOptions = {
        python: { status: 'active', pythonPath: '/path/to/python' },
        config: new Map([['server.installBehavior', 'nothing']]),
        systemCommands: new Map([
          ['/path/to/python -m esbonio --version', ['', 'no such module esbonio']]
        ])
      }

      let server = makeServerManager(editorOptions)
      let version = await server.getServerVersion('0.15.0', new Date(Date.now()))

      assert.deepStrictEqual(undefined, version)
    })
  })

  suite("shouldInstall()", () => {

    test('installBehavior = nothing: it should abort the setup', async () => {
      let server = makeServerManager()
      let nextAction = await server.shouldInstall('nothing')

      assert.deepStrictEqual(nextAction, 0 /* Abort */)
    })

    test('installBehavior = automatic: it should continue the setup', async () => {
      let server = makeServerManager()
      let nextAction = await server.shouldInstall('automatic')

      assert.deepStrictEqual(nextAction, 2 /* Continue */)
    })

    test('installBehavior = prompt(user cancels): it should abort the setup', async () => {
      let editorOptions: MockEditorOptions = {
        warningMessages: new Map(
          [["The Esbonio Language Server is not installed", undefined]]
        )
      }


      let server = makeServerManager(editorOptions)
      let nextAction = await server.shouldInstall('prompt')

      assert.deepStrictEqual(nextAction, 0 /* Abort */)
    })

    test('installBehavior = prompt(user selects no): it should abort the setup', async () => {
      let editorOptions: MockEditorOptions = {
        warningMessages: new Map(
          [["The Esbonio Language Server is not installed", { title: "No" }]]
        )
      }

      let server = makeServerManager(editorOptions)
      let nextAction = await server.shouldInstall('prompt')

      assert.deepStrictEqual(nextAction, 0 /* Abort */)
    })

    test('installBehavior = prompt(user selects yes): it should continue the setup', async () => {
      let editorOptions: MockEditorOptions = {
        warningMessages: new Map(
          [["The Esbonio Language Server is not installed", { title: "Yes" }]]
        )
      }

      let server = makeServerManager(editorOptions)
      let nextAction = await server.shouldInstall('prompt')

      assert.deepStrictEqual(nextAction, 2 /* Continue */)
    })

    test('installBehavior = prompt(user selects switch): it should retry the setup', async () => {
      let editorOptions: MockEditorOptions = {
        warningMessages: new Map(
          [["The Esbonio Language Server is not installed", { title: "Switch Environments" }]]
        )
      }

      let server = makeServerManager(editorOptions)
      let nextAction = await server.shouldInstall('prompt')
      assert.deepStrictEqual(nextAction, 1 /* Continue */)
    })
  })

})
