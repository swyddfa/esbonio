import * as path from "path";
import * as Mocha from "mocha";
import * as glob from "glob";

const mocha = new Mocha({
  ui: 'tdd',
  color: true
})

const testsRoot = path.resolve(__dirname, 'unit')

glob('**/**.test.js', { cwd: testsRoot }, (err, files) => {
  if (err) {
    throw err
  }

  files.forEach(f => mocha.addFile(path.resolve(testsRoot, f)))

  mocha.run(failures => {
    if (failures > 0) {
      throw new Error(`${failures} tests failed.`)
    }
  })
})
