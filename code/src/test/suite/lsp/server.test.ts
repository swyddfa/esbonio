import * as assert from "assert";
import { shouldPromptUpdate, shouldUpdate } from "../../../lsp/server";

suite("ServerManager", () => {

  suite("shouldUpdate", () => {
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

  suite("shouldPromptUpdate", () => {
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