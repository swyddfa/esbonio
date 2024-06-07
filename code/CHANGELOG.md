## v0.94.2 - 2024-06-07


### Misc

- Fix release pipeline ([#831](https://github.com/swyddfa/esbonio/issues/831))


## v0.94.1 - 2024-06-07


### Misc

- Update bundled version of the language server to `v1.0.0b5` ([#831](https://github.com/swyddfa/esbonio/issues/831))


## v0.94.0 - 2024-04-28


### Breaking Changes

- The `Open Preview to the Side` and `Open Preview` commands have been renamed to `Preview Documentation in Split Window` and `Preview Documentation` respectively. ([#780](https://github.com/swyddfa/esbonio/issues/780))

### Enhancements

- Esbonio now adds an icon to the editor toolbar that opens the preview in markdown files. ([#780](https://github.com/swyddfa/esbonio/issues/780))
- The preview pane will now show a "No Content Found" message if the file could not be previewed.
  The message contains troubleshooting steps on how the preview might be fixed. ([#793](https://github.com/swyddfa/esbonio/issues/793))

### Misc

- Esbonio now depends on the [MyST Syntax Highlighting](https://marketplace.visualstudio.com/items?itemName=chrisjsewell.myst-tml-syntax) extension. ([#794](https://github.com/swyddfa/esbonio/issues/794))


## v0.93.2 - 2024-04-22


### Fixes

- Fix pipeline to publish to Open VSX ([#777](https://github.com/swyddfa/esbonio/issues/777))


## v0.93.1 - 2024-04-20


### Fixes

- Rebuild extension to pull in the latest esbonio release ([#775](https://github.com/swyddfa/esbonio/issues/775))


## v0.93.0 - 2024-04-20


### Breaking Changes

- - Removed the `esbonio.server.logLevel` option, use `esbonio.logging.level` instead.
  - Removed the `esbonio.server.logFilter` option, it has been made obselete by the other `esbonio.logging.*` options

  ([#748](https://github.com/swyddfa/esbonio/issues/748))
- The `esbonio.server.enabledInPyFiles` configuration option has been removed, use `esbonio.server.documentSelector` instead ([#756](https://github.com/swyddfa/esbonio/issues/756))

### Enhancements

- Added the following configuration options

  - `esbonio.logging.level`, set the default logging level of the server
  - `esbonio.logging.format`, set the default format of server log messages
  - `esbonio.logging.filepath`, enable logging to a file
  - `esbonio.logging.stderr`, print log messages to stderr
  - `esbonio.logging.window`, send log messages as `window/logMessage` notifications
  - `esbonio.logging.config`, override logging configuration for individual loggers, see the [documentation](https://docs.esbon.io/en/latest/lsp/reference/configuration.html#lsp-configuration-logging) for details
  - `esbonio.trace.server` enables the logging of LSP messages sent to/from the server

  ([#748](https://github.com/swyddfa/esbonio/issues/748))
- Added the `esbonio.server.documentSelector` option, granting the user fine grained control over which files the server is enabled in. ([#756](https://github.com/swyddfa/esbonio/issues/756))

### Fixes

- The extension will now notify the server when the user changes Python environment via the Python extension ([#703](https://github.com/swyddfa/esbonio/issues/703))


## v0.92.1 - 2024-01-15


### Misc

- Fix release pipeline ([#720](https://github.com/swyddfa/esbonio/issues/720))


## v0.92.0 - 2024-01-15


### Breaking Changes

- The following server configuration options have been removed as they are no longer required.

  - `esbonio.server.installBehavior`
  - `esbonio.server.updateBehavior`
  - `esbonio.server.updateFrequency`

  The language server is now bundled as part of the VSCode extension itself, so a separate installation step is no longer necessary.

  The following sphinx configuration options have been removed

  - `esbonio.server.hideSphinxOutput`
  - `esbonio.sphinx.buildDir`
  - `esbonio.sphinx.builderName`
  - `esbonio.sphinx.confDir`
  - `esbonio.sphinx.doctreeDir`
  - `esbonio.sphinx.forceFullBuild`
  - `esbonio.sphinx.keepGoing`
  - `esbonio.sphinx.makeMode`
  - `esbonio.sphinx.numJobs`
  - `esbonio.sphinx.quiet`
  - `esbonio.sphinx.silent`
  - `esbonio.sphinx.srcDir`
  - `esbonio.sphinx.tags`
  - `esbonio.sphinx.verbosity`
  - `esbonio.sphinx.warningIsError`

  The Sphinx application instance is now launched using a standard `sphinx-build` command line provided through the `esbonio.sphinx.buildCommand` option, so individual options are no longer necessary.
  **Note:** The `esbonio.sphinx.configOverrides` option has been preserved as it can be easier to use than the equivalent command line options.

  ([#619](https://github.com/swyddfa/esbonio/issues/619))
- The minimum required VSCode version is now 1.82.0 ([#666](https://github.com/swyddfa/esbonio/issues/666))

### Enhancements

- The following server configuration values have been added

  - `esbonio.server.enableDevTools`: Enable integration with [lsp-devtools](https://github.com/swyddfa/lsp-devtools) for the language server itself.

  The following sphinx configuration values have been added

  - `esbonio.sphinx.buildCommand`: Set the `sphinx-build` command to use when invoking the Sphinx subprocess

  - `esbonio.sphinx.pythonCommand`: By default, the extension will attempt to reuse the Python environment you have configured in the Python extension when invoking Sphinx.
    This option can be used to override this behavior.

  - `esbonio.sphinx.cwd`: The working directory from which to launch the Sphinx process

  - `esbonio.sphinx.envPassthrough`: A list of envrionment variables to pass through to the Sphinx process.

  - `esbonio.sphinx.enableDevTools`: Enable integration with [lsp-devtools](https://github.com/swyddfa/lsp-devtools) for the sphinx process

    - `esbonio.sphinx.pythonPath`: Used to override the Python packages (typically `esbonio.sphinx_agent`) that are injected into the Sphinx environment

  The following preview related options have been added

  - `esbonio.sphinx.enableSyncScrolling`: Enable support for syncronised scrolling between the editor and preview pane
  - `esbonio.preview.bind`: Set the network interface that the preview server binds to
  - `esbonio.preview.httpPort`: Set the port number the HTTP server binds to
  - `esbonio.preview.wsPort`: Set the port number the WebSocket server binds to

  ([#626](https://github.com/swyddfa/esbonio/issues/626))

### Misc

- Updated the bundled version of `esbonio` to `1.0.0b1` ([#720](https://github.com/swyddfa/esbonio/issues/720))


# v0.11.0 - 2023-03-06

## Features

- It should now be possible to run the Sphinx based language server in <https://vscode.dev>!

  Note, that this functionality, is still **experimental**.
  To try it out, you will need to explicity set the `esbonio.sphinx.confDir` option to `/<github-user>/<github-repo>/<path>/`.
  For example, this project would need it to be set to `/swyddfa/esbonio/docs/`. ([#548](https://github.com/swyddfa/esbonio/issues/548))

# v0.10.6 - 2023-02-04

## Enhancements

- Add `esbonio.server.completion.preferredInsertBehavior` option.
  Controls how completions behave when accepted, the following values are supported.

  - `replace` (default)

    > Accepted completions will replace existing text, allowing the server to rewrite the current line in place.
    > This allows the server to return all possible completions within the current context.
    > In this mode the server will set the `textEdit` field of a `CompletionItem`.

  - `insert`

    > Accepted completions will append to existing text rather than replacing it.
    > Since rewriting is not possible, only the completions that are compatible with any existing text will be returned.
    > In this mode the server will set the `insertText` field of a `CompletionItem` which should work better with editors that do no support `textEdits`. ([#471](https://github.com/swyddfa/esbonio/issues/471))

- Add `esbonio.server.enableDevTools` option.

  This new flag indended for developers, when enabled, will wrap the language server in the [lsp-devtools](https://github.com/swyddfa/lsp-devtools) agent, enabling the use of some extra tooling.

  It is on the developer to ensure the required dependencies are installed. ([#532](https://github.com/swyddfa/esbonio/issues/532))

## Misc

- Bump `vscode-languageclient` to 8.x ([#485](https://github.com/swyddfa/esbonio/issues/485))

# v0.10.5 - 2022-11-05

## Misc

- Ensure npm deps are installed in release pipeline ([#482](https://github.com/swyddfa/esbonio/issues/482))

# v0.10.4 - 2022-11-05

## Misc

- Fix VSCode packaging step in release pipeline ([#481](https://github.com/swyddfa/esbonio/issues/481))

# v0.10.3 - 2022-11-05

## Misc

- Fix broken release pipeline ([#480](https://github.com/swyddfa/esbonio/issues/480))

# v0.10.2 - 2022-11-05

## Fixes

- The extension no longer shows an annoying second error notification when you dismiss install/update requests. ([#286](https://github.com/swyddfa/esbonio/issues/286))
- An error while checking for the latest release of the language server no longer prevents the existing server from starting. ([#454](https://github.com/swyddfa/esbonio/issues/454))
- Language status items should no longer disappear on Windows when configured using explicit filepaths. ([#458](https://github.com/swyddfa/esbonio/issues/458))
- The preview panel should now open on Windows when configured with explicit file paths ([#466](https://github.com/swyddfa/esbonio/issues/466))

## Enhancements

- Add `esbonio.server.showDeprecationWarnings` option.

  This is flag is primarily aimed at developers working either directly on esbonio, or one of its extensions.
  When enabled, any warnings (such as `DeprecationWarnings`) will be logged and published to the client as diagnostics. ([#443](https://github.com/swyddfa/esbonio/issues/443))

- The extension now gives the option for you to disable the language server when it requests you install/update it. ([#468](https://github.com/swyddfa/esbonio/issues/468))

## Misc

- The default value for the `esbonio.server.updateFrequency` setting has been changed to `never`. ([#454](https://github.com/swyddfa/esbonio/issues/454))

# v0.10.1 - 2022-09-07

## Removed

- The reStructuredText Syntax Highlighting extension is no longer included via VSCode's "Extension Pack" feature as these rules are now distributed with VSCode itself. ([#447](https://github.com/swyddfa/esbonio/issues/447))

# v0.10.0 - 2022-08-02

## Features

- Initial **very experimental** web extension support!
  Currently this is limited to the vanilla docutils language server available in the `esbonio` Python package - so no Sphinx support yet.

  The outline view,  basic completions and hovers for vanilla docutils roles and directives are the only known working features at this point. ([#438](https://github.com/swyddfa/esbonio/issues/438))

## Enhancements

- Log output in the `Esbonio` output channel is now syntax highlighted. ([#436](https://github.com/swyddfa/esbonio/issues/436))

# v0.9.2 - 2022-06-07

## Fixes

- The `esbonio.server.pythonPath` setting now accepts paths relative to `${workspaceFolder}`.

  **Note** This is simply an alias for the existing `${workspaceRoot}` functionality. ([#404](https://github.com/swyddfa/esbonio/issues/404))

# v0.9.1 - 2022-05-25

## Fixes

- The correct value of the `esbonio.sphinx.doctreeDir` setting is used when constructing the initializationOptions to send to the server. ([#390](https://github.com/swyddfa/esbonio/issues/390))

## Enhancements

- Language status items are now shown in a project's `conf.py`, while also correctly being omitted for rst files not under the project's `srcDir` ([#391](https://github.com/swyddfa/esbonio/issues/391))

# v0.9.0 - 2022-05-22

## Features

- Add new `esbonio.sphinx.copyBuildCommand` and `esbonio.sphinx.setBuildCommand` commands.
  As the name suggests, the first command will copy the equivalent `sphinx-build` command to the clipboard while the set build command prompts for a set of `sphinx-build` arguments and updates the server's configuration accordingly. ([#360](https://github.com/swyddfa/esbonio/issues/360))

## Deprecated

- The `esbonio.server.hideSphinxOutput` option has been deprecated in favour of the new `esbonio.sphinx.quiet` and `esbonio.sphinx.silent` options.
  It will be removed when the server reaches `v1.0` ([#360](https://github.com/swyddfa/esbonio/issues/360))

## Misc

- The `esbonio.sphinx.numJobs` configuration now defaults to `1` in line with `sphinx-build` defaults. ([#374](https://github.com/swyddfa/esbonio/issues/374))

# v0.8.3 - 2022-04-20

## Misc

- Switch from `vscode-test` to `@vscode/test-electron` ([#372](https://github.com/swyddfa/esbonio/issues/372))

# v0.8.2 - 2022-04-18

## Enhancements

- Added the `esbonio.sphinx.forceFullBuild` option (default: `true`) which can be used to control if the language server forces a full Sphinx build on startup. ([#358](https://github.com/swyddfa/esbonio/issues/358))
- Added the `esbonio.sphinx.numJobs` option (default: `auto`) which can be used to control the number of parallel jobs used by Sphinx. ([#359](https://github.com/swyddfa/esbonio/issues/359))

# v0.8.1 - 2022-03-22

## Fixes

- Fix handling of Windows URIs in preview code. ([#340](https://github.com/swyddfa/esbonio/issues/340))

# v0.8.0 - 2022-03-17

## Features

- Add commands `esbonio.sphinx.selectConfDir`, `esbonio.sphinx.selectSrcDir`, `esbonio.sphinx.selectBuildDir`
  which allow the user to interactively select values for the `esbonio.sphinx.confDir`, `esbonio.sphinx.srcDir`, `esbonio.sphinx.buildDir`
  options.

  The commands can be triggered through the command palette or the language status items. ([#337](https://github.com/swyddfa/esbonio/issues/337))

## Fixes

- Language status items now correctly remove the errored status when an issue is resolved. ([#329](https://github.com/swyddfa/esbonio/issues/329))

## Enhancements

- Switched to an `<iframe>` based approach for previews, which should improve compatability with various Sphinx themes. ([#275](https://github.com/swyddfa/esbonio/issues/275))

## Misc

- Renamed the `esbonio.server.entryPoint` configuration option to `esbonio.server.startupModule` ([#337](https://github.com/swyddfa/esbonio/issues/337))

## Removed

- The editor commands `esbonio.insert.link` and `esbonio.insert.inlineLink` have been removed.
  They are however available in the [reStructuredText](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext) extension. ([#307](https://github.com/swyddfa/esbonio/issues/307))

# v0.7.3 - 2022-03-07

## Fixes

- Duplicate output channels are no longer created in the event of a language server crash. ([#287](https://github.com/swyddfa/esbonio/issues/287))
- Changes to `esbonio.server.logLevel` no longer require VSCode to be restarted to take effect client side. ([#301](https://github.com/swyddfa/esbonio/issues/301))
- Options such as `esboino.server.logLevel` can now be set on a per-project basis. ([#302](https://github.com/swyddfa/esbonio/issues/302))

## Enhancements

- The status bar has been re-implemented as a collection of language status items. ([#240](https://github.com/swyddfa/esbonio/issues/240))
- The server can now be restarted by clicking on the relevant language status item ([#241](https://github.com/swyddfa/esbonio/issues/241))
- Add option `esbonio.server.enabledInPyFiles` which allows the user to disable the language server in Python files. ([#285](https://github.com/swyddfa/esbonio/issues/285))
- All extension log output has been unified into a single output channel. ([#287](https://github.com/swyddfa/esbonio/issues/287))
- Add option `esbonio.server.entryPoint` which allows the user to set an entry point.
  Also add options `esbonio.server.includedModules` and `esbonio.server.excludedModules` to allow the user to control which modules are loaded in the server configuration. ([#288](https://github.com/swyddfa/esbonio/issues/288))
- The `esbonio.server.pythonPath` configuration option now supports paths relative to `${workspaceRoot}` ([#300](https://github.com/swyddfa/esbonio/issues/300))

## Misc

- Add soft dependency on [trond-snekvik.simple-rst](https://marketplace.visualstudio.com/items?itemName=trond-snekvik.simple-rst) in favour of using bespoke grammar rules. ([#279](https://github.com/swyddfa/esbonio/issues/279))
- This extension now requires the Esbonio language server version to be `>= 0.9.0` ([#308](https://github.com/swyddfa/esbonio/issues/308))

# v0.7.2 - 2021-11-26

## Fixes

- Simplified highlighting of footnote references to prevent edge cases from
  effectively disabling highlighting of a document. ([#252](https://github.com/swyddfa/esbonio/issues/252))
- Literal block markers no longer disable highlighting of any preceeding content. ([#254](https://github.com/swyddfa/esbonio/issues/254))
- Code blocks that have injected grammars (e.g. python code blocks) now correctly highlight any options
  on the directive ([#255](https://github.com/swyddfa/esbonio/issues/255))

## Enhancements

- Add `esbonio.server.enabled` option which gives the user the ability to disable the language sever if they wish. ([#239](https://github.com/swyddfa/esbonio/issues/239))
- Code blocks that contain a language that's not recognised, are now highlighted as strings. ([#253](https://github.com/swyddfa/esbonio/issues/253))
- Add `esbonio.sphinx.buildDir` option which allows the user to specify where Sphinx's build files get written to. ([#258](https://github.com/swyddfa/esbonio/issues/258))

# v0.7.1 - 2021-09-13

## Fixes

- Fix handling of `<script>` tags without a `src` attribute when generating the
  HTML preview of a page. ([#214](https://github.com/swyddfa/esbonio/issues/214))

## Enhancements

- When the user is using an environment with an incompatible Python version but have
  the Python extension available, they are given the option of picking a new environment to use. ([#176](https://github.com/swyddfa/esbonio/issues/176))
- When the user is prompted to install the language server in the current environment,
  they now also have the option of picking a new environment to use instead. ([#224](https://github.com/swyddfa/esbonio/issues/224))

## Misc

- This extension does not support untrusted workspaces. ([#217](https://github.com/swyddfa/esbonio/issues/217))

# v0.7.0 - 2021-06-05

## Features

- Add the ability to preview the output from the `html` builder.\` ([#190](https://github.com/swyddfa/esbonio/issues/190))
- Add a statusbar item that indicates the state of the language server. ([#194](https://github.com/swyddfa/esbonio/issues/194))
- VSCode will now syntax highlight C, C++, Javascript and Typescript code blocks ([#205](https://github.com/swyddfa/esbonio/issues/205))

## Fixes

- Fix incorrect syntax highlighting of multiple links on a single line ([#203](https://github.com/swyddfa/esbonio/issues/203))
- VSCode now treats `*` characters as quotes, meaning selecting some text and entering
  a `*` will automatically surround that text rather than replacing it. ([#204](https://github.com/swyddfa/esbonio/issues/204))

## Misc

- The cli arguments `--cache-dir`, `--log-filter`, `--log-level` and
  `--hide-sphinx-output` have been replaced with the configuration
  parameters `esbonio.sphinx.buildDir`, `esbonio.server.logFilter`,
  `esbonio.logLevel` and `esbonio.server.hideSphinxOutput` respectively ([#185](https://github.com/swyddfa/esbonio/issues/185))
- The language server's startup sequence has been reworked. Language clients are now
  required to provide configuration parameters under the `initializationOptions` field
  in the `initialize` request. ([#192](https://github.com/swyddfa/esbonio/issues/192))

# v0.6.2 - 2021-05-14

## Fixes

- Fix minimum required language server version ([#183](https://github.com/swyddfa/esbonio/issues/183))

# v0.6.1 - 2021-05-13

## Fixes

- Literal blocks now have the correct syntax highlighting ([#138](https://github.com/swyddfa/esbonio/issues/138))
- The language server is now reloaded when the Python environment is changed. ([#140](https://github.com/swyddfa/esbonio/issues/140))
- It's now possible to test dev builds of the language server with the extension ([#168](https://github.com/swyddfa/esbonio/issues/168))

## Misc

- Improvements to the development experience ([#170](https://github.com/swyddfa/esbonio/issues/170))

# v0.6.0 - 2021-05-07

## Features

- Add new `esbonio.sphinx.confDir` option that allows for a project's config
  directory to be explictly set should the automatic discovery in the Language
  Server fail. ([#63](https://github.com/swyddfa/esbonio/issues/63))
- Add new `esbonio.sphinx.srcDir` option that allows for overriding the
  language server's assumption that source files are located in the same
  place as the `conf.py` file. ([#142](https://github.com/swyddfa/esbonio/issues/142))

## Fixes

- Editor keybindings now only apply in `*.rst` files. ([#141](https://github.com/swyddfa/esbonio/issues/141))

## Misc

- Update `vscode-languageclient` to v7.0.0 ([#152](https://github.com/swyddfa/esbonio/issues/152))

# v0.5.1 - 2021-03-01

## Misc

- Fix release pipeline ([#135](https://github.com/swyddfa/esbonio/issues/135))

# v0.5.0 - 2021-03-01

## Features

- Add new `esbonio.server.installBehavior` option that gives greater control
  over how Language Server installation is handled. `automatic` will install the
  server in new environments without prompting, `prompt` will ask for
  confirmation first and `nothing` disables installation entirely.\` ([#92](https://github.com/swyddfa/esbonio/issues/92))
- Expose `esbonio.server.logFilter` option that can be used to limit the
  components of the language server which produce output. ([#118](https://github.com/swyddfa/esbonio/issues/118))
- Expose `esbonio.server.hideSphinxOutput` option which allows for Sphinx's
  build output to be omitted from the log. ([#120](https://github.com/swyddfa/esbonio/issues/120))
- The extension will now automatically restart the Language Server when the
  extension's configuration is updated ([#122](https://github.com/swyddfa/esbonio/issues/122))
- `css`, `html`, `json` and `yaml` code blocks are now syntax highlighted. ([#125](https://github.com/swyddfa/esbonio/issues/125))

## Fixes

- The extension now checks that the configured Python verison is compatible with
  the Language Server. ([#97](https://github.com/swyddfa/esbonio/issues/97))
- Fix syntax higlighting for namespaced roles (e.g. `:py:func:`) and directives
  (e.g. `.. py:function::`) ([#98](https://github.com/swyddfa/esbonio/issues/98))
- Invalid literals are no longer highlighted as valid syntax ([#99](https://github.com/swyddfa/esbonio/issues/99))
- Ensure that the Language Server uses the latest config options when restarted ([#121](https://github.com/swyddfa/esbonio/issues/121))
- The extension now enforces a minimum Language Server version ([#123](https://github.com/swyddfa/esbonio/issues/123))
- Fixed syntax highlighting of footnotes. ([#124](https://github.com/swyddfa/esbonio/issues/124))
- Fix syntax highlighting where sentences containing ellipses were incorrectly
  identified as a comment ([#126](https://github.com/swyddfa/esbonio/issues/126))
- Invalid bold text (e.g. `** invalid**`) is no longer highlighted as valid
  syntax. ([#127](https://github.com/swyddfa/esbonio/issues/127))
- Invalid italic text (e.g. `*invalid *`) is no longer highlighted as valid
  syntax. ([#128](https://github.com/swyddfa/esbonio/issues/128))

## Misc

- The language server's logging level is set to match the logging level defined in
  the extension. ([#86](https://github.com/swyddfa/esbonio/issues/86))
- The extension now makes use of the `--cache-dir` cli option in the language
  server to set Sphinx's build output to use a known location. ([#119](https://github.com/swyddfa/esbonio/issues/119))
- If `esbonio.server.logLevel` is set to `debug` the extension assumes the
  user is working on the Language Server and will automatically open the log panel
  on restarts. ([#133](https://github.com/swyddfa/esbonio/issues/133))

# v0.4.0 - 2021-02-03

## Features

- Expose an `esbonio.log.level` config option that allows the level of logging
  output to be configured ([#85](https://github.com/swyddfa/esbonio/issues/85))
- Add `esbonio.server.updateFrequency` option that controls how often the
  extension should check for updates. Valid values are `daily`, `weekly`,
  `monthly` and `` never` `` ([#88](https://github.com/swyddfa/esbonio/issues/88))
- Add `esbonio.server.updateBehavior` option that controls how updates should be
  applied. Valid values are `promptAlways`, `promptMajor` and `automatic` ([#89](https://github.com/swyddfa/esbonio/issues/89))

## Fixes

- Fix edge cases around syntax highlighting bold/italic elements. ([#47](https://github.com/swyddfa/esbonio/issues/47))
- The extension now activates when it detects a sphinx project ([#49](https://github.com/swyddfa/esbonio/issues/49))
- The language client now also listens to changes in Python files so that we can
  pick up changes in the project's `` conf.py` `` ([#50](https://github.com/swyddfa/esbonio/issues/50))
- Fix edge cases around syntax highlighting inline code snippets ([#70](https://github.com/swyddfa/esbonio/issues/70))

# v0.3.1 - 2020-12-14

## Misc

- Fix `vsix` packaging so that grammar tests are not included. ([#44](https://github.com/swyddfa/esbonio/issues/44))

# v0.3.0 - 2020-12-14

## Features

- Add 2 commands that can be used to insert links. One that uses the inline syntax
  {kbd}`Alt+L`, the other, the named reference syntax {kbd}`Alt+Shift+L` ([#37](https://github.com/swyddfa/esbonio/issues/37))
- Add command that will restart the language server ([#39](https://github.com/swyddfa/esbonio/issues/39))

## Fixes

- Support syntax highligting for more header styles. Support highligting python code
  under directives from Sphinx's `sphinx.ext.doctest` extension ([#42](https://github.com/swyddfa/esbonio/issues/42))

# v0.2.1 - 2020-11-28

## Misc

- The published `vsix` now contains a changelog in a format that's compatible with the
  VSCode marketplace. ([#16](https://github.com/swyddfa/esbonio/issues/16))
- The published `vsix` package now only contains the files that are necessary. ([#17](https://github.com/swyddfa/esbonio/issues/17))
- The extension is now bundled into a single file using webpack ([#18](https://github.com/swyddfa/esbonio/issues/18))

# v0.2.0 - 2020-11-27

## Features

- If there is no Python interpreter configured and the
  [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
  is available, then esbonio will now use the interpreter that's been configured for the
  Python extension ([#9](https://github.com/swyddfa/esbonio/issues/9))

# v0.1.0 - 2020-11-23

## Features

- If the language server is not installed, the extension will now prompt to install it.
  It will also prompt to update it when new versions are available. ([#12](https://github.com/swyddfa/esbonio/issues/12))

## Misc

- Update build pipeline to use `towncrier` to autogenerate release notes and changelog
  entries ([#10](https://github.com/swyddfa/esbonio/issues/10))
