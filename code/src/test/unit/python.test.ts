import * as assert from "assert";
import { PythonManager } from "../../node/lsp/python";
import { ConsoleLogger } from "../../node/core/log";
import { mockEditorIntegrations } from "../mock";

const logger = new ConsoleLogger()

suite("PythonManager", () => {

  suite('getCmd()', () => {

    test("it should use the Python extension's Python if available", async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'active', pythonPath: '/path/to/python' },
        config: new Map()
      })

      let python = new PythonManager(editor, logger)
      let command = await python.getCmd()
      assert.deepStrictEqual(command, ['/path/to/python'])
    })

    test("it should prefer the user provided Python over the Python extension", async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'active', pythonPath: '/python/extension/python' },
        config: new Map([["server.pythonPath", "/usr/provided/python"]])
      })

      let python = new PythonManager(editor, logger)
      let command = await python.getCmd()
      assert.deepStrictEqual(command, ['/usr/provided/python'])
    })

    test("it should correctly handle ${workspaceRoot}", async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'active', pythonPath: '/python/extension/python' },
        config: new Map([["server.pythonPath", "${workspaceRoot}/venv/bin/python"]]),
        workspaces: [{ uri: "file:///workspace", fsPath: "/workspace" }]
      })

      let python = new PythonManager(editor, logger)
      let command = await python.getCmd()
      assert.deepStrictEqual(command, ['/workspace/venv/bin/python'])
    })

    // NOTE: This cannot truly be correct until we implement multi-root support
    test("it should 'correctly' handle ${workspaceFolder}", async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'active', pythonPath: '/python/extension/python' },
        config: new Map([["server.pythonPath", "${workspaceFolder}/venv/bin/python"]]),
        workspaces: [{ uri: "file:///workspace", fsPath: "/workspace" }]
      })

      let python = new PythonManager(editor, logger)
      let command = await python.getCmd()
      assert.deepStrictEqual(command, ['/workspace/venv/bin/python'])
    })
  })

  suite('getVersion()', () => {

    test('it should show an error if no Python evironment is configured', async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'unavailable' },
        errorMessages: new Map(
          [['Unable to run Python command, no environment configured.', undefined]]
        ),
      })

      let python = new PythonManager(editor, logger)
      await python.getVersion()
    })

    test('it should make sure the Python version is valid', async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'active', pythonPath: '/path/to/python' },
        systemCommands: new Map([
          [
            '/path/to/python -c import sys ; print("{0.major}.{0.minor}.{0.micro}".format(sys.version_info))',
            ["not-a-version", ""]
          ]
        ]),
      })

      let python = new PythonManager(editor, logger)
      let version = await python.getVersion()
      assert.strictEqual(undefined, version)
    })

    test('it should return the version', async () => {
      let editor = mockEditorIntegrations({
        python: { status: 'active', pythonPath: '/path/to/python' },
        systemCommands: new Map([
          [
            '/path/to/python -c import sys ; print("{0.major}.{0.minor}.{0.micro}".format(sys.version_info))',
            ["3.7.4   ", ""]
          ]
        ]),
      })

      let python = new PythonManager(editor, logger)
      let version = await python.getVersion()
      assert.strictEqual('3.7.4', version)
    })
  })
})
