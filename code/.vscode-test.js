const { defineConfig } = require('@vscode/test-cli');
const fs = require('fs');
const { join } = require('path');
const { tmpdir } = require('os');

const DEMO_WORKSPACE = '../lib/esbonio/tests/workspaces/demo'

/**
 * Create an instance of the given workspace under /tmp with the given config values.
 *
 * @param {string} src the directory to copy the workspace from
 * @param {string} name the name of the workspace
 * @param {any} config config values to write
 */
function createWorkspaceWithConfig(src, name, config) {
  let dest = fs.mkdtempSync(join(tmpdir(), `${name}-`));

  console.log(`Copying ${src} workspace to ${dest}`);
  fs.cpSync(src, dest, { recursive: true });

  fs.mkdirSync(join(dest, '.vscode'));
  fs.writeFileSync(join(dest, '.vscode', 'settings.json'), JSON.stringify(config, null, 2));

  return dest
}

// Just the demo folder.

module.exports = defineConfig([
  {
    label: 'E2E Tests',
    files: 'dist/test/**/*.test.js',
    workspaceFolder: createWorkspaceWithConfig(DEMO_WORKSPACE, "python-extension", {
      "esbonio.logger.level": "debug",
      "esbonio.server.enabled": false  // Don't start server by default, the tests will do it.
    }),
    mocha: {
      ui: 'tdd',
      timeout: 20000
    }
  }
]);
