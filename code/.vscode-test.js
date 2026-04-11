const { defineConfig } = require('@vscode/test-cli');
const fs = require('fs');
const path = require('path');
const { tmpdir } = require('os');

const ESBONIO_PKG = path.resolve("../lib/esbonio")
const REQUIREMENTS = path.resolve("./requirements-libs.txt")
const DEMO_WORKSPACE = '../lib/esbonio/tests/workspaces/demo'
const MOCHA_ARGS = {reporter: 'min', ui: 'tdd', timeout: 20000}

/**
 * Create an instance of the given workspace under /tmp with the given config values.
 *
 * @param {string} src the directory to copy the workspace from
 * @param {string} name the name of the workspace
 * @param {any} config config values to write
 */
function createWorkspaceWithConfig(src, name, config) {
  let base = path.join(tmpdir(), "esbonio-vsc-e2e-tests")
  if (!fs.existsSync(base)) {
    fs.mkdirSync(base)
  }

  let dest = fs.mkdtempSync(path.join(base, `${name}-`));

  console.log(`Copying ${src} workspace to ${dest}`);
  fs.cpSync(src, dest, { recursive: true });

  fs.mkdirSync(path.join(dest, '.vscode'));
  fs.writeFileSync(path.join(dest, '.vscode', 'settings.json'), JSON.stringify(config, null, 2));

  return dest
}

module.exports = defineConfig([
  {
    label: 'Defaults', // Using the Python extension to grab any Python interpreter, using bundled Sphinx env.
    files: 'dist/test/**/*.test.js',
    workspaceFolder: createWorkspaceWithConfig(DEMO_WORKSPACE, "python-extension-bundled", {
      "esbonio.logging.level": "debug",
      "esbonio.logging.filepath": "esbonio.log",
      "esbonio.server.enabled": false
    }),
    env: {
      ESBONIO_LOG_DEST: 'console',
      EXPECTED_SPHINX_VERSION: "8.1.3",
      EXPECTED_SPHINX_THEME: "alabaster.css"
    },
    mocha: MOCHA_ARGS,
  },
  {
    label: 'Python 3.10', // Using uv to install esbonio under 3.10, using bundled Sphinx env.
    files: 'dist/test/**/*.test.js',
    workspaceFolder: createWorkspaceWithConfig(DEMO_WORKSPACE, "uv-3.10-bundled", {
      "esbonio.logging.level": "debug",
      "esbonio.logging.filepath": "esbonio.log",
      "esbonio.server.enabled": false,
      "esbonio.server.pythonCommand": [
        "uv", "run", "--no-project", "--python", "3.10",
        "--with-requirements", REQUIREMENTS,
        "--with", ESBONIO_PKG,
        "python"
      ]
    }),
    env: {
      ESBONIO_LOG_DEST: 'console',
      EXPECTED_SPHINX_VERSION: "8.1.3",
      EXPECTED_SPHINX_THEME: "alabaster.css",
      EXPECTED_PYTHON_VERSION: "3.10"
    },
    mocha: MOCHA_ARGS,
  },
  {
    label: 'Python 3.11', // Using uv to install esbonio under 3.11, using bundled Sphinx env.
    files: 'dist/test/**/*.test.js',
    workspaceFolder: createWorkspaceWithConfig(DEMO_WORKSPACE, "uv-3.11-bundled", {
      "esbonio.logging.level": "debug",
      "esbonio.logging.filepath": "esbonio.log",
      "esbonio.server.enabled": false,
      "esbonio.server.pythonCommand": [
        "uv", "run", "--no-project", "--python", "3.11",
        "--with-requirements", REQUIREMENTS,
        "--with", ESBONIO_PKG,
        "python"
      ]
    }),
    env: {
      ESBONIO_LOG_DEST: 'console',
      EXPECTED_SPHINX_VERSION: "8.1.3",
      EXPECTED_SPHINX_THEME: "alabaster.css",
      EXPECTED_PYTHON_VERSION: "3.11"
    },
    mocha: MOCHA_ARGS,
  },
  {
    label: 'Python 3.12', // Using uv to install esbonio under 3.12, using bundled Sphinx env.
    files: 'dist/test/**/*.test.js',
    workspaceFolder: createWorkspaceWithConfig(DEMO_WORKSPACE, "uv-3.12-bundled", {
      "esbonio.logging.level": "debug",
      "esbonio.logging.filepath": "esbonio.log",
      "esbonio.server.enabled": false,
      "esbonio.server.pythonCommand": [
        "uv", "run", "--no-project", "--python", "3.12",
        "--with-requirements", REQUIREMENTS,
        "--with", ESBONIO_PKG,
        "python"
      ]
    }),
    env: {
      ESBONIO_LOG_DEST: 'console',
      EXPECTED_SPHINX_VERSION: "8.1.3",
      EXPECTED_SPHINX_THEME: "alabaster.css",
      EXPECTED_PYTHON_VERSION: "3.12"
    },
    mocha: MOCHA_ARGS,
  },
  {
    label: 'Python 3.13', // Using uv to install esbonio under 3.13, using bundled Sphinx env.
    files: 'dist/test/**/*.test.js',
    workspaceFolder: createWorkspaceWithConfig(DEMO_WORKSPACE, "uv-3.13-bundled", {
      "esbonio.logging.level": "debug",
      "esbonio.logging.filepath": "esbonio.log",
      "esbonio.server.enabled": false,
      "esbonio.server.pythonCommand": [
        "uv", "run", "--no-project", "--python", "3.13",
        "--with-requirements", REQUIREMENTS,
        "--with", ESBONIO_PKG,
        "python"
      ]
    }),
    env: {
      ESBONIO_LOG_DEST: 'console',
      EXPECTED_SPHINX_VERSION: "8.1.3",
      EXPECTED_SPHINX_THEME: "alabaster.css",
      EXPECTED_PYTHON_VERSION: "3.13"
    },
    mocha: MOCHA_ARGS,
  },
  {
    label: 'Python 3.14', // Using uv to install esbonio under 3.14, using bundled Sphinx env.
    files: 'dist/test/**/*.test.js',
    workspaceFolder: createWorkspaceWithConfig(DEMO_WORKSPACE, "uv-3.14-bundled", {
      "esbonio.logging.level": "debug",
      "esbonio.logging.filepath": "esbonio.log",
      "esbonio.server.enabled": false,
      "esbonio.server.pythonCommand": [
        "uv", "run", "--no-project", "--python", "3.14",
        "--with-requirements", REQUIREMENTS,
        "--with", ESBONIO_PKG,
        "python"
      ]
    }),
    env: {
      ESBONIO_LOG_DEST: 'console',
      EXPECTED_SPHINX_VERSION: "8.1.3",
      EXPECTED_SPHINX_THEME: "alabaster.css",
      EXPECTED_PYTHON_VERSION: "3.14"
    },
    mocha: MOCHA_ARGS,
  },
  {
    label: 'Python 3.14, Custom Sphinx', // Using uv to install esbonio under 3.14, using custom Sphinx env.
    files: 'dist/test/**/*.test.js',
    workspaceFolder: createWorkspaceWithConfig(DEMO_WORKSPACE, "uv-3.14-custom", {
      "esbonio.logging.level": "debug",
      "esbonio.logging.filepath": "esbonio.log",
      "esbonio.server.enabled": false,
      "esbonio.server.pythonCommand": [
        "uv", "run", "--no-project", "--python", "3.14",
        "--with-requirements", REQUIREMENTS,
        "--with", ESBONIO_PKG, "python"
      ],
      "esbonio.sphinx.pythonCommand": [
        "uv", "run", "--no-project", "--python", "3.14",
        "--with", "sphinx==9.1.0",
        "--with", "myst-parser",
        "--with", "furo",
        "--with", "sphinx-design",
        "python"
      ],
    }),
    env: {
      ESBONIO_LOG_DEST: 'console',
      EXPECTED_SPHINX_VERSION: "9.1.0",
      EXPECTED_SPHINX_THEME: "furo.css",
      EXPECTED_PYTHON_VERSION: "3.14"
    },
    mocha: MOCHA_ARGS,
  },
]);
