importScripts("https://cdn.jsdelivr.net/pyodide/v0.22.1/full/pyodide.js")

import * as path from 'path';

/* @ts-ignore */
import * as languageServer from "./server.py"

function patchedStdout(data) {
  if (!data.trim()) {
    return
  }

  const message = JSON.parse(data)

  console.debug(message)
  postMessage(message)
}

async function initPyodide() {
  console.debug("Initializing pyodide")

  /* @ts-ignore */
  let pyodide = await loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.22.1/full/"
  })

  return pyodide
}

let SERVER_STARTED = false
async function startServer(pyodide) {
  console.debug("Installing dependencies.")
  await pyodide.loadPackage(["micropip"])
  await pyodide.runPythonAsync(`
  import sys
  import micropip

  await micropip.install('setuptools')
  await micropip.install('esbonio')
  `)

  console.debug("Loading server.")

  pyodide.globals.get('sys').stdout.write = patchedStdout
  await pyodide.runPythonAsync(languageServer)
  SERVER_STARTED = true
}


/**
 * Write a file's contents into pyodide's in-memory filesystem.
 *
 * Since the VSCode api returns a Uint8 array, let's use lower level
 * file system APIs to avoid round tripping the data to a string and
 * back.
 *
 * It *should* also let us ignore annoying details like encodings :)
 *
 * @param pyodide The pyodide instance to use.
 * @param message The message containing the file's contents
 */
async function writeFile(pyodide, message) {

  const FS = pyodide.FS
  const fpath = message.fileUri.path
  const ppath = message.parentUri.path

  mkdirs(FS, ppath)

  let stream = FS.open(fpath, 'w+')
  let data = message.content

  console.debug(`Writing file: ${fpath}`)
  FS.write(stream, data, 0, data.length, 0)
  FS.close(stream)
}

function mkdirs(FS, dir: string) {

  try {
    FS.stat(dir)
  } catch (err) {
    // Dir does not exist
    let parent = path.dirname(dir)

    try {
      FS.stat(parent)
    } catch (err) {
      mkdirs(FS, parent)
    }

    FS.mkdir(dir)
  }
}

const pyodideReady = initPyodide()

onmessage = async (event) => {
  let message = event.data
  console.debug(message)

  let pyodide = await pyodideReady

  // Pass regular LSP messages to the language server.
  if (message.jsonrpc) {

    if (!SERVER_STARTED) {
      await startServer(pyodide)
    }

    /* @ts-ignore */
    self.client_message = JSON.stringify(message)
    await pyodide.runPythonAsync(`
    import json
    from js import client_message

    message = json.loads(client_message, object_hook=server.lsp._deserialize_message)
    server.lsp._procedure_handler(message)
    `)

    return
  }

  // Otherwise, handle out-of-spec messages here.
  switch (message.op) {
    case "writeFile":
      await writeFile(pyodide, message)
      break
    default:
      console.error(`Unknown operation: ${message.op}`)
  }

}
