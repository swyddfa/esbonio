const { defineConfig } = require('@vscode/test-cli');

module.exports = defineConfig([
  {
    label: 'E2E Tests',
    files: 'dist/test/**/*.test.js',
    workspaceFolder: '../lib/esbonio/tests/workspaces/demo',
    mocha: {
      ui: 'tdd',
      timeout: 20000
    }
  }
]);
