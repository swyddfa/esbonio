## v1.0.0b3 - 2024-04-28


### Features

- Add support for role completions in MyST documents ([#775](https://github.com/swyddfa/esbonio/issues/775))

### Enhancements

- If the client supports it, the server will now send `window/showDocument` requests when previewing a file.

  The server will automatically react to changes to ``esbonio.preview.*`` configuration options. ([#793](https://github.com/swyddfa/esbonio/issues/793))

### Fixes

- The server should once again, correctly guess a reasonable basic `sphinx-build` build command for projects located in a sub-folder of the workspace ([#779](https://github.com/swyddfa/esbonio/issues/779))
- The server should once again automatically trigger a build when previewing a file, when necessary ([#783](https://github.com/swyddfa/esbonio/issues/783))


## v1.0.0b2 - 2024-04-20


### Breaking Changes

- - Removed the `esbonio.server.logLevel` option, use `esbonio.logging.level` instead.
  - Removed the `esbonio.server.logFilter` option, it has been made obselete by the other `esbonio.logging.*` options

  ([#748](https://github.com/swyddfa/esbonio/issues/748))

### Enhancements

- Added the following configuration options

  - `esbonio.logging.level`, set the default logging level of the server
  - `esbonio.logging.format`, set the default format of server log messages
  - `esbonio.logging.filepath`, enable logging to a file
  - `esbonio.logging.stderr`, print log messages to stderr
  - `esbonio.logging.window`, send log messages as `window/logMessage` notifications
  - `esbonio.logging.config`, override logging configuration for individual loggers, see the [documentation](https://docs.esbon.io/en/latest/lsp/reference/configuration.html#lsp-configuration-logging) for details

  ([#748](https://github.com/swyddfa/esbonio/issues/748))
- The server will now automatically restart the underlying Sphinx process when it detects a change in its configuration ([#750](https://github.com/swyddfa/esbonio/issues/750))
- The server now emits `sphinx/clientCreated`, `sphinx/clientErrored` and `sphinx/clientDestroyed` notifications that correspond to the lifecycle of the underlying Sphinx process ([#756](https://github.com/swyddfa/esbonio/issues/756))

### Fixes

- The server should no longer sometimes spawn duplicated Sphinx processes ([#660](https://github.com/swyddfa/esbonio/issues/660))
- The server now respects Sphinx configuration values like `suppress_warnings` ([#695](https://github.com/swyddfa/esbonio/issues/695))
- The server will no longer raise a `ValueError` when used in a situation where there is an empty workspace ([#718](https://github.com/swyddfa/esbonio/issues/718))


## v1.0.0b1 - 2024-01-15


### Breaking Changes

- Removed `esbonio.lsp.spelling` module, though it will be available as `esbonio.ext.spelling` via the `esbonio-extensions` package. ([#583](https://github.com/swyddfa/esbonio/issues/583))
- Drop Python 3.7 support ([#584](https://github.com/swyddfa/esbonio/issues/584))
- Drop Sphinx 4.x support ([#585](https://github.com/swyddfa/esbonio/issues/585))

### Features

- The language server now supports reading configuration values from `workspace/configuration` requests and `pyproject.toml` files.
  When supported by the client, the server can detect and respond to changes in (most) configuration automatically - no more manually restarting the server! ([#527](https://github.com/swyddfa/esbonio/issues/527))
- The language server now supports `workspace/symbol` requests ([#611](https://github.com/swyddfa/esbonio/issues/611))
- Sphinx build progress is now reported using the `window/workDoneProgress/create` API ([#659](https://github.com/swyddfa/esbonio/issues/659))
- For the clients that support the pull diagnostics model, the server now supports the `textDocument/diagnostic` and `workspace/diagnostic` methods. ([#689](https://github.com/swyddfa/esbonio/issues/689))
- The language server can now provide completion suggestions for MyST directives. ([#706](https://github.com/swyddfa/esbonio/issues/706))

### Enhancements

- When providing completion suggestions for directives, `esbonio` now takes the `.. default-domain::` directive into account ([#105](https://github.com/swyddfa/esbonio/issues/105))

### Fixes

- Fix path separator character on Windows by @ExaneServerTeam ([#719](https://github.com/swyddfa/esbonio/issues/719))


## v0.16.2 - 2023-10-07

This somewhat quiet release marks the end of the `0.x` series as development has now shifted to focus on what will ultimately become the `1.0` release.

In fact this release includes a sneaky preview of the `1.0` version of the server - which includes support for multi-root projects!
If you are feeling adventurous and want to try it out - change the command you use to launch `esbonio` to `python -m esbonio.server`

However, to set expectations there are \<em>many\</em> missing features from the preview server.
The only features currently available are sphinx builds, diagnostics, document symbols and live preview/sync scrolling - but they should all work across multiple roots/projects!

See [this issue](https://github.com/swyddfa/esbonio/issues/609") for more information and if you want to submit any feedback and keep an eye out for some beta releases in the not-to-distant-future!

### Enhancements

- When creating a Sphinx application instance, the language server will now look in all workspace folders choosing the first valid configuration it finds.
  Failing that it will revert to its original behavior of looking in the `workspaceRoot` given by the client. ([#467](https://github.com/swyddfa/esbonio/issues/467))

### Fixes

- The server will no longer fail to handle the `initialize` request when clients set `initializationOptions` to `null` ([#586](https://github.com/swyddfa/esbonio/issues/586))

### Misc

- Replace `appdirs` with `platformdirs` by @coloursofnoise ([#621](https://github.com/swyddfa/esbonio/issues/621))

## v0.16.1 - 2023-02-18

### Fixes

- With live previews enabled, `esbonio` should no longer conflict with Sphinx extensions that register their own `source-read` handlers. ([#539](https://github.com/swyddfa/esbonio/issues/539))

## v0.16.0 - 2023-02-04

### Features

- Add new `server.completion.preferredInsertBehavior` option.
  This allows the user to indicate to the server how they would prefer completions to behave when accepted.

  The default value is `replace` and corresponds to the server's current behavior where completions replace existing text.
  In this mode the server will set the `textEdit` field of a `CompletionItem`.

  This release also introduces a new mode `insert`, where completions will append to existing text rather than replacing it.
  This also means that only the completions that are compatible with any existing text will be returned.
  In this mode the server will set the `insertText` field of a `CompletionItem` which should work better with editors that do no support `textEdits`.

  **Note:** This option is only a hint and the server will not ensure that it is followed, though it is planned for all first party completion suggestions to (eventually) respect this setting.
  As of this release, all completion suggestions support `replace`  and role, directive and directive option completions support `insert`. ([#471](https://github.com/swyddfa/esbonio/issues/471))

### Documentation

- Add getting started guide for Sublime Text by @vkhitrin ([#522](https://github.com/swyddfa/esbonio/issues/522))

### API Changes

- `CompletionContext` objects now expose a `config` field that contains any user supplied configuration values affecting completions. ([#531](https://github.com/swyddfa/esbonio/issues/531))

### Misc

- Drop Python 3.6 support ([#400](https://github.com/swyddfa/esbonio/issues/400))

- Migrate to pygls `v1.0`

  There are some breaking changes, but only if you use Esbonio's extension APIs, if you simply use the language server in your favourite editor you *shouldn't* notice a difference.

  The most notable change is the replacement of `pydantic` type definitions with `attrs` and `cattrs` via the new [lsprotocol](https://github.com/microsoft/lsprotocol) package.
  For more details see pygls' [migration guide](https://pygls.readthedocs.io/en/latest/pages/migrating-to-v1.html). ([#484](https://github.com/swyddfa/esbonio/issues/484))

- Drop support for Sphinx 3.x

  Add support for Sphinx 6.x ([#523](https://github.com/swyddfa/esbonio/issues/523))

## v0.15.0 - 2022-12-03

### Features

- Add initial support for synced scrolling and live previews of HTML builds.
  **Note** Both of these features rely on additional integrations outside of the LSP protocol therefore requiring dedicated support from clients.

  Synced scrolling support can be enabled by setting the `server.enableScrollSync` initialization option to `True` and works by injecting line numbers into the generated HTML which a client can use to align the preview window to the source window.

  Live preview support can be enabled by setting the `server.enableLivePreview` initialization option to `True`, the language server will then pass the contents of unsaved files for Sphinx to build.
  Currently clients are responsible for triggering intermediate builds with the new `esbonio.server.build` command, though this requirement may be removed in future. ([#490](https://github.com/swyddfa/esbonio/issues/490))

### Enhancements

- Completion suggestions will now also be generated for the long form (`:py:func:`) of roles and directives in the primary and standard Sphinx domains. ([#416](https://github.com/swyddfa/esbonio/issues/416))
- The language server should now populate the `serverInfo` fields of its response to a client's `initialize` request. ([#497](https://github.com/swyddfa/esbonio/issues/497))
- The default `suggest_options` implementation for `DirectiveLanguageFeatures` should now be more useful in that it will return the keys from a directive's `option_spec` ([#498](https://github.com/swyddfa/esbonio/issues/498))
- The language server now recognises and returns `DocumentLinks` for `image::` and `figure::` directives that use `http://` or `https://` references for images. ([#506](https://github.com/swyddfa/esbonio/issues/506))

### Fixes

- Fix handling of deprecation warnings in Python 3.11 ([#494](https://github.com/swyddfa/esbonio/issues/494))

- The language server should now correctly handle errors that occur while generating completion suggestions for a directive's options

  The language server should now show hovers for directives in the primary domain. ([#498](https://github.com/swyddfa/esbonio/issues/498))

- Errors thrown by `DirectiveLanguageFeatures` during `textDocument/documentLink` or `textDocument/definition` requests are now caught and no longer result in frustrating error banners in clients.

  The `textDocument/documentLink` handler for `image::` and `figure::` should no longer throw exceptions for invalid paths on Windows. ([#506](https://github.com/swyddfa/esbonio/issues/506))

### API Changes

- `RoleLanguageFeatures` have been introduced as the preferred method of extending role support going forward.
  Subclasses can be implement any of the following methods

  - `complete_targets` called when generating role target completion items
  - `find_target_definitions` used to implement goto definition for role targets
  - `get_implementation` used to get the implementation of a role given its name
  - `index_roles` used to tell the language server which roles exist
  - `resolve_target_link` used to implement document links for role targets
  - `suggest_roles` called when generating role completion suggestions

  and are registered using the new `Roles.add_feature()` method. ([#495](https://github.com/swyddfa/esbonio/issues/495))

### Deprecated

- The following protocols have been deprecated and will be removed in `v1.0`

  - `TargetDefinition`
  - `TargetCompletion`
  - `TargetLink`

  The following methods have been deprecated and will be removed in `v1.0`

  - `Roles.add_target_definition_provider`
  - `Roles.add_target_link_provider`
  - `Roles.add_target_completion_provider`
  - `RstLanguageServer.get_roles()`
  - `SphinxLanguageServer.get_domain()`
  - `SphinxLanguageServer.get_domains()`
  - `SphinxLanguageServer.get_roles()`
  - `SphinxLanguageServer.get_role_target_types()`
  - `SphinxLanguageServer.get_role_targets()`
  - `SphinxLanguageServer.get_intersphinx_targets()`
  - `SphinxLanguageServer.has_intersphinx_targets()`
  - `SphinxLanguageServer.get_intersphinx_projects()` ([#495](https://github.com/swyddfa/esbonio/issues/495))

## v0.14.3 - 2022-11-05

### Misc

- Fix broken release pipeline ([#480](https://github.com/swyddfa/esbonio/issues/480))

## v0.14.2 - 2022-11-05

### Enhancements

- Add `esbonio.server.showDeprecationWarnings` option.

  This is flag is primarily aimed at developers working either directly on esbonio, or one of its extensions.
  When enabled, any warnings (such as `DeprecationWarnings`) will be logged and published to the client as diagnostics. ([#443](https://github.com/swyddfa/esbonio/issues/443))

### Fixes

- Spinx log messages are no longer duplicated after refreshing the application instance ([#460](https://github.com/swyddfa/esbonio/issues/460))

### API Changes

- Added `add_diagnostics` method to the `RstLanguageServer` to enable adding diagnostics to a document incrementally. ([#443](https://github.com/swyddfa/esbonio/issues/443))

- The `Directives` language feature can now be extended by registering `DirectiveLanguageFeatures` using the new `add_feature` method.
  This is now the preferred extension mechanism and should be used by all extensions going forward. ([#444](https://github.com/swyddfa/esbonio/issues/444))

- `DirectiveLanguageFeatures` can now implement the following methods.

  - `index_directives`: used to discover available directive implementations
  - `suggest_directives`: used to determine which directive names can be suggested in the current completion context (`function` vs `py:function` vs `c:function` etc.)
  - `get_implementation`: used to go from a directive name (`function` vs `py:function`) to its implementation
  - `suggest_options`: used to determine which directive options can be suggested in the current completion context ([#453](https://github.com/swyddfa/esbonio/issues/453))

### Deprecated

- `ArgumentCompletion`, `ArgumentDefinition` and `ArgumentLink` directive providers have been deprecated in favour of `DirectiveLanguageFeatures` and will be removed in `v1.0` ([#444](https://github.com/swyddfa/esbonio/issues/444))

- Calling the `get_directives()` method on the `RstLanguageServer` and `SphinxLanguageServer` objects is deprecated in favour of calling the `get_directives()` method on the `Directives` language feature.
  It will be removed in `v1.0`

  Calling the `get_directive_options()` method on the `RstLanguageServer` and `SphinxLanguageServer` objects deprecated and will be removed in `v1.0`. ([#453](https://github.com/swyddfa/esbonio/issues/453))

### Misc

- Add Python 3.11 support ([#470](https://github.com/swyddfa/esbonio/issues/470))

## v0.14.1 - 2022-09-11

### Fixes

- `textDocument/documentSymbol` requests should no longer fail on substitution definitions. ([#448](https://github.com/swyddfa/esbonio/issues/448))

## v0.14.0 - 2022-07-31

### Features

- The language server now supports `textDocument/implementation` requests for roles and directives. ([#431](https://github.com/swyddfa/esbonio/issues/431))

### Enhancements

- Line numbers for diagnostics for issues found within Python docstrings should now be more accurate. ([#433](https://github.com/swyddfa/esbonio/issues/433))
- Document symbol requests made for unsaved files now use the language client's version rather than the version on disk. ([#434](https://github.com/swyddfa/esbonio/issues/434))

### Fixes

- Diagnostics for issues found in `.. included::` files should now have the correct filepath. ([#425](https://github.com/swyddfa/esbonio/issues/425))
- Extensions defined within Sphinx extensions or `conf.py` files can now take advantage of dependency injection ([#428](https://github.com/swyddfa/esbonio/issues/428))
- The server should now handle document symbol requests for files that are treated as reStructuredText files by a language client but don't have an `*.rst` extension. ([#434](https://github.com/swyddfa/esbonio/issues/434))

### API Changes

- It is now possible to manually load an extension by calling the `load_extension` method on a language server object. ([#429](https://github.com/swyddfa/esbonio/issues/429))
- `LanguageFeatures` can now respond to `textDocument/implementation` requests by providing an `implementation` method and a collection of `implementation_triggers`. ([#431](https://github.com/swyddfa/esbonio/issues/431))

## v0.13.1 - 2022-06-29

### Fixes

- Log messages from Sphinx's startup are now captured and forwarded onto the language client. ([#408](https://github.com/swyddfa/esbonio/issues/408))
- Log messages from the server's startup are now captured and forwarded onto the language client. ([#417](https://github.com/swyddfa/esbonio/issues/417))
- Fixed handling of default roles when getting a document's initial doctree. ([#418](https://github.com/swyddfa/esbonio/issues/418))

### API Changes

- Improved type annotations allow `rst.get_feature` to be called with a language feature's type and have the return type match accordingly. This should allow editors to provide better autocomplete suggestions etc. ([#409](https://github.com/swyddfa/esbonio/issues/409))

- `esbonio_setup` functions can now request specific language features and servers, just by providing type annotations e.g:

  ```
  from esbonio.lsp.roles import Roles
  from esbonio.lsp.sphinx import SphinxLanguageServer

  def esbonio_setup(rst: SphinxLanguageServer, roles: Roles):
      ...
  ```

  This function will then only be called when the language server is actually an instance of `SphinxLanguageServer` and only when that lanuage server instance contains an intance of the `Roles` feature. ([#410](https://github.com/swyddfa/esbonio/issues/410))

### Deprecated

- Calling `rst.get_feature` with a string will become an error in `v.1.0`, a language feature's class should be given instead. ([#409](https://github.com/swyddfa/esbonio/issues/409))

## v0.13.0 - 2022-05-27

### Features

- Add initial `textDocument/hover` support, with documentation for roles and directives being shown.

  Add `>` to completion triggers. ([#311](https://github.com/swyddfa/esbonio/issues/311))

### Fixes

- The language server now correctly handles diagnosics originating from `.. c:function::` directives. ([#393](https://github.com/swyddfa/esbonio/issues/393))

## v0.12.0 - 2022-05-22

### Features

- The language server now supports many (but not all) `sphinx-build` command line options.
  The `sphinx.*` section of the server's initialization options has been extened to include the following options.

  - `configOverrides`
  - `doctreeDir`
  - `keepGoing`
  - `makeMode`
  - `quiet`
  - `silent`
  - `tags`
  - `verbosity`
  - `warningIsError`

  See the [documentation](https://swyddfa.github.io/esbonio/docs/latest/en/lsp/getting-started.html#configuration) for details.

  Additionally, a new cli application `esbonio-sphinx` is now available which language clients (or users) can use to convert `sphinx-build` cli options to/from the server's initialization options. ([#360](https://github.com/swyddfa/esbonio/issues/360))

### Enhancements

- `textDocument/documentSymbol` responses now include symbol information on directives. ([#374](https://github.com/swyddfa/esbonio/issues/374))

### Fixes

- `.. include::` directives no longer break goto definition for `:ref:` role targets ([#361](https://github.com/swyddfa/esbonio/issues/361))

### API Changes

- Add method `get_initial_doctree` to `RstLanguageServer` which can be used to obtain a doctree of the given file before any role and directives have been applied. ([#374](https://github.com/swyddfa/esbonio/issues/374))

### Misc

- The `esbonio.sphinx.numJobs` configuration now defaults to `1` in line with `sphinx-build` defaults. ([#374](https://github.com/swyddfa/esbonio/issues/374))

## v0.11.2 - 2022-05-09

### Enhancements

- Add `esbonio.lsp.rst._record` and `esbonio.lsp.sphinx._record` startup modules.
  These can be used to record all LSP client-sever communication to a text file. ([#380](https://github.com/swyddfa/esbonio/issues/380))

### Fixes

- The language server now detects functionality bundled with standard Sphinx extensions ([#381](https://github.com/swyddfa/esbonio/issues/381))

## v0.11.1 - 2022-04-26

### Fixes

- `textDocument/documentLink` requests no longer fail when encountering `::` characters in C++ references. ([#377](https://github.com/swyddfa/esbonio/issues/377))

## v0.11.0 - 2022-04-18

### Features

- Add `textDocument/documentLink` support.

  The server supports resolving links for role targets with initial support for intersphinx references and local `:doc:` references.

  The server also supports resolving links for directive arguments with initial support for `.. image::`, `.. figure::`, `.. include::` and `.. literalinclude::` directives. ([#294](https://github.com/swyddfa/esbonio/issues/294))

### Enhancements

- Language clients can now control if the server forces a full build of a Sphinx project on startup by providing a `sphinx.forceFullBuild` initialization option, which defaults to `true` ([#358](https://github.com/swyddfa/esbonio/issues/358))
- Language clients can now control the number of parallel jobs by providing a `sphinx.numJobs` initialization option, which defaults to `auto`. Clients can disable parallel builds by setting this option to `1` ([#359](https://github.com/swyddfa/esbonio/issues/359))

### Fixes

- Goto definition for `:ref:` targets now works for labels containing `-` characters ([#357](https://github.com/swyddfa/esbonio/issues/357))
- Goto definition for `:doc:` targets will now only return a result if the referenced document actually exists. ([#369](https://github.com/swyddfa/esbonio/issues/369))

## v0.10.3 - 2022-04-07

### Fixes

- A client's capabilities is now respected when constructing `CompletionItems` ([#270](https://github.com/swyddfa/esbonio/issues/270))
- Instead of spamming the client with notifications, the language server now reports Sphinx config/build errors as diagnostics. ([#315](https://github.com/swyddfa/esbonio/issues/315))
- Previews should now work on MacOS ([#341](https://github.com/swyddfa/esbonio/issues/341))
- Running `$ esbonio` directly on the command line now correctly starts the server again ([#346](https://github.com/swyddfa/esbonio/issues/346))
- The language server should no longer fail when suggesting completions for directives that are not class based.
  e.g. `DirectiveContainer` based directives from the `breathe` extension. ([#353](https://github.com/swyddfa/esbonio/issues/353))

## v0.10.2 - 2022-03-22

### Fixes

- Previews on Windows should now start correctly ([#341](https://github.com/swyddfa/esbonio/issues/341))

## v0.10.1 - 2022-03-20

### Fixes

- The language server should now correctly handle `buildDir`, `confDir` and `srcDir` config values containing paths relative to `~` ([#342](https://github.com/swyddfa/esbonio/issues/342))

## v0.10.0 - 2022-03-17

### Features

- The server now provides an `esbonio.server.preview` command that can be used to preview HTML Sphinx projects via a local HTTP server. ([#275](https://github.com/swyddfa/esbonio/issues/275))
- The language server now accepts paths relative to `${workspaceFolder}` for Sphinx's `confDir`, `srcDir` and `builDir` options. ([#304](https://github.com/swyddfa/esbonio/issues/304))
- The language server now supports `textDocument/definition` requests for `.. image::` directive arguments. ([#318](https://github.com/swyddfa/esbonio/issues/318))
- The language server now supports `textDocument/definition` requests for `.. figure::` directive arguments. ([#319](https://github.com/swyddfa/esbonio/issues/319))
- The language server will now look in sphinx extension modules and `conf.py` files for extensions to the language server. ([#331](https://github.com/swyddfa/esbonio/issues/331))

### Fixes

- The language server no longer crashes when asked to `--exclude` a module that would not be loaded anyway. ([#313](https://github.com/swyddfa/esbonio/issues/313))
- Completion suggestions for domain objects referenced by roles such as `:doc:`, `:ref:`, `:func:` and many more now correctly update each time a rebuild is triggered. ([#317](https://github.com/swyddfa/esbonio/issues/317))
- Goto definition on a directive's arguments is no longer foiled by trailing whitespace. ([#327](https://github.com/swyddfa/esbonio/issues/327))

## v0.9.0 - 2022-03-07

### Features

- The language server now supports providing documentation on roles, directives (and their options).
  Note however, this requires the relevant documentation to be explicitly added to the relevant `LanguageFeatures`. ([#36](https://github.com/swyddfa/esbonio/issues/36))
- The server now listens for `workspace/didDeleteFiles` notifications. ([#93](https://github.com/swyddfa/esbonio/issues/93))
- Add experimental spell checking support. ([#271](https://github.com/swyddfa/esbonio/issues/271))
- The language server now provides completion suggestions for `.. code-block::` and `.. highlight::` language names. ([#273](https://github.com/swyddfa/esbonio/issues/273))
- The language server now supports `completionItem/resolve` requests, it is currently implemented for roles, directives and directive options. ([#274](https://github.com/swyddfa/esbonio/issues/274))
- The language server now supports `textDocument/definition` requests for `.. include::` directive arguments. ([#276](https://github.com/swyddfa/esbonio/issues/276))
- The language server now supports `textDocument/definition` requests for `.. literalinclude::` directive arguments. ([#277](https://github.com/swyddfa/esbonio/issues/277))

### Fixes

- Diagnostics are now cleared for deleted files. ([#291](https://github.com/swyddfa/esbonio/issues/291))

## v0.8.0 - 2021-11-26

### Features

- The language server now respects the project's `default_role` setting. ([#72](https://github.com/swyddfa/esbonio/issues/72))
- Initial implementation of the `textDocument/documentSymbols` request which for example, powers the "Outline" view in VSCode.
  Currently only section headers are returned. ([#242](https://github.com/swyddfa/esbonio/issues/242))
- The `esbonio.sphinx.buildDir` option now supports `${workspaceRoot}` and `${confDir}` variable expansions ([#259](https://github.com/swyddfa/esbonio/issues/259))

### Fixes

- Role target `CompletionItems` now preserve additional cross reference modifiers like `!` and `~` ([#211](https://github.com/swyddfa/esbonio/issues/211))
- Intersphinx projects are now only suggested if they contain targets relevant to the current role. ([#244](https://github.com/swyddfa/esbonio/issues/244))
- Variables are now properly substituted in diagnostic messages. ([#246](https://github.com/swyddfa/esbonio/issues/246))

## v0.7.0 - 2021-09-13

### Features

- Add initial goto definition support.
  Currently only support definitions for `:ref:` and `:doc:` role targets. ([#209](https://github.com/swyddfa/esbonio/issues/209))

### Fixes

- Completion suggestions for `:option:` targets now insert text in the correct format (`<progname> <option>`) ([#212](https://github.com/swyddfa/esbonio/issues/212))
- Diagnostics are now correctly cleared on Windows ([#213](https://github.com/swyddfa/esbonio/issues/213))
- Completion suggestions are no longer given in the middle of Python code. ([#215](https://github.com/swyddfa/esbonio/issues/215))
- `CompletionItems` should no longer corrupt existing text when selected. ([#223](https://github.com/swyddfa/esbonio/issues/223))

### Misc

- Updated `pygls` to `v0.11.0` ([#218](https://github.com/swyddfa/esbonio/issues/218))

## v0.6.2 - 2021-06-05

### Fixes

- The language server now correctly handles windows file URIs when determining Sphinx's
  build directory. ([#184](https://github.com/swyddfa/esbonio/issues/184))
- Role and role target completions are now correctly generated when the role
  is being typed within parenthesis e.g. `(:kbd:...` ([#191](https://github.com/swyddfa/esbonio/issues/191))
- Path variables like `${confDir}` and `${workspaceRoot}` are now properly expanded
  even when there are no additional path elements. ([#208](https://github.com/swyddfa/esbonio/issues/208))

### Misc

- The cli arguments `--cache-dir`, `--log-filter`, `--log-level` and
  `--hide-sphinx-output` have been replaced with the configuration
  parameters `esbonio.sphinx.buildDir`, `esbonio.server.logFilter`,
  `esbonio.logLevel` and `esbonio.server.hideSphinxOutput` respectively ([#185](https://github.com/swyddfa/esbonio/issues/185))
- The language server's startup sequence has been reworked. Language clients are now
  required to provide configuration parameters under the `initializationOptions` field
  in the `initialize` request. ([#192](https://github.com/swyddfa/esbonio/issues/192))
- The language server will now send an `esbonio/buildComplete` notification to
  clients when it has finished (re)building the docs. ([#193](https://github.com/swyddfa/esbonio/issues/193))
- An entry for `esbonio` has been added to the `console_scripts`
  entry point, so it's now possible to launch the language server by
  calling `esbonio` directly ([#195](https://github.com/swyddfa/esbonio/issues/195))

## v0.6.1 - 2021-05-13

### Fixes

- Intersphinx projects are now only included as completion suggestions for roles
  which target object types in a project's inventory. ([#158](https://github.com/swyddfa/esbonio/issues/158))
- Fix the uri representation of Windows paths when reporting diagnostics ([#166](https://github.com/swyddfa/esbonio/issues/166))
- The language server now attempts to recreate the Sphinx application if the user
  updates a broken `conf.py`. ([#169](https://github.com/swyddfa/esbonio/issues/169))
- The language server no longer crashes if clients don't send the `esbonio.sphinx`
  configuration object ([#171](https://github.com/swyddfa/esbonio/issues/171))
- Docstrings from Sphinx and Docutils' base directive classes are no longer
  included in completion suggestions as they are not useful. ([#178](https://github.com/swyddfa/esbonio/issues/178))
- Sphinx build time exceptions are now caught and reported ([#179](https://github.com/swyddfa/esbonio/issues/179))
- Fix `Method not found: $/setTrace` exceptions when running against VSCode ([#180](https://github.com/swyddfa/esbonio/issues/180))

## v0.6.0 - 2021-05-07

### Features

- The Language Server will now offer filepath completions for the `image`,
  `figure`, `include` and `literalinclude` directives as well as the
  `download` role. ([#34](https://github.com/swyddfa/esbonio/issues/34))
- Language clients can now override the default `conf.py` discovery mechanism
  by providing a `esbonio.sphinx.confDir` config option. ([#62](https://github.com/swyddfa/esbonio/issues/62))
- Language clients can now override the assumption that Sphinx's `srcdir`
  is the same as its `confdir` by providing a `esbonio.sphinx.srcDir`
  config option. ([#142](https://github.com/swyddfa/esbonio/issues/142))

### Fixes

- The Language Server no longer throws an exception while handling errors raised
  during initialization of a Sphinx application. ([#139](https://github.com/swyddfa/esbonio/issues/139))
- The Language Server now correctly offers completions for `autoxxx` directive options
  ([#100](https://github.com/swyddfa/esbonio/issues/100))

### Misc

- Upgrage pygls to v0.10.x ([#144](https://github.com/swyddfa/esbonio/issues/144))

## v0.5.1 - 2021-04-20

### Fixes

- Pin `pygls<0.10.0` to ensure installs pick up a compatible version ([#147](https://github.com/swyddfa/esbonio/issues/147))

## v0.5.0 - 2021-02-25

### Features

- The language server now reports invalid references as diagnostics ([#57](https://github.com/swyddfa/esbonio/issues/57))
- Add `--log-level` cli argument that allows Language Clients to
  control the verbosity of the Language Server's log output. ([#87](https://github.com/swyddfa/esbonio/issues/87))
- Directive completions are now domain aware. ([#101](https://github.com/swyddfa/esbonio/issues/101))
- Role and role target completions are now domain aware. ([#104](https://github.com/swyddfa/esbonio/issues/104))
- Intersphinx completions are now domain aware ([#106](https://github.com/swyddfa/esbonio/issues/106))
- Add `log-filter` cli argument that allows Language Clients to choose
  which loggers they want to recieve messages from. Also add
  `--hide-sphinx-output` cli argument that can suppress Sphinx's build
  log as it it handled separately. ([#113](https://github.com/swyddfa/esbonio/issues/113))
- Add `-p`, `--port` cli arguments that start the Language Server in
  TCP mode while specifying the port number to listen on. ([#114](https://github.com/swyddfa/esbonio/issues/114))
- Add `--cache-dir` cli argument that allows Language Clients to
  specify where cached data should be stored e.g. Sphinx's build output. ([#115](https://github.com/swyddfa/esbonio/issues/115))

### Fixes

- The language server now reloads when the project's `conf.py` is modified ([#83](https://github.com/swyddfa/esbonio/issues/83))
- `$/setTraceNotification` notifications from VSCode no longer cause exceptions to be thrown
  in the Language Server. ([#91](https://github.com/swyddfa/esbonio/issues/91))
- Consistency errors are now included in reported diagnostics. ([#94](https://github.com/swyddfa/esbonio/issues/94))
- Ensure `:doc:` completions are specified relative to the project root. ([#102](https://github.com/swyddfa/esbonio/issues/102))

## v0.4.0 - 2021-02-01

### Features

- Directive option completions are now provided
  within a directive's options block ([#36](https://github.com/swyddfa/esbonio/issues/36))
- For projects that use `interpshinx` completions
  for intersphinx targets are now suggested when available ([#74](https://github.com/swyddfa/esbonio/issues/74))

### Fixes

- Regex that catches diagnostics from Sphinx's
  output can now handle windows paths. Diagnostic reporting now sends a
  proper URI ([#66](https://github.com/swyddfa/esbonio/issues/66))
- Diagnostics are now reported on first startup ([#68](https://github.com/swyddfa/esbonio/issues/68))
- Fix exception that was thrown when trying to find
  completions for an unknown role type ([#73](https://github.com/swyddfa/esbonio/issues/73))
- The server will not offer completion suggestions outside of
  a role target ([#77](https://github.com/swyddfa/esbonio/issues/77))

## v0.3.0 - 2021-01-27

### Features

- Errors in Sphinx's build output are now parsed and published
  to the LSP client as diagnostics ([#35](https://github.com/swyddfa/esbonio/issues/35))
- Directive completions now include a snippet that
  prompts for any required arguments ([#58](https://github.com/swyddfa/esbonio/issues/58))

### Fixes

- Errors encountered when initialising Sphinx are now caught and the language
  client is notified of an issue. ([#33](https://github.com/swyddfa/esbonio/issues/33))
- Fix issue where some malformed `CompletionItem` objects were
  preventing completion suggestions from being shown. ([#54](https://github.com/swyddfa/esbonio/issues/54))
- Windows paths are now handled correctly ([#60](https://github.com/swyddfa/esbonio/issues/60))
- Server no longer chooses `conf.py` files that
  are located under a `.tox` or `site-packages` directory ([#61](https://github.com/swyddfa/esbonio/issues/61))

## v0.2.1 - 2020-12-08

### Fixes

- Directives that are part of the `std` or `py` Sphinx domains
  will now be included in completion suggestions ([#31](https://github.com/swyddfa/esbonio/issues/31))

## v0.2.0 - 2020-12-06

### Features

- Python log events can now published to Language Clients ([#27](https://github.com/swyddfa/esbonio/issues/27))
- Sphinx's build output is now redirected to the LSP client as log
  messages. ([#28](https://github.com/swyddfa/esbonio/issues/28))
- Suggest completions for targets for a number of roles from the
  [std](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#the-standard-domain)
  and [py](https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#the-python-domain)
  domains including `ref`, `doc`, `func`, `meth`, `class` and more. ([#29](https://github.com/swyddfa/esbonio/issues/29))

### Fixes

- Fix discovery of roles so that roles in Sphinx domains are used and
  that unimplemented `docutils` roles are not surfaced. ([#26](https://github.com/swyddfa/esbonio/issues/26))

## v0.1.2 - 2020-12-01

### Misc

- Use `ubuntu-20.04` for Python builds so that the correct version of `pandoc` is
  available ([#25](https://github.com/swyddfa/esbonio/issues/25))

## v0.1.1 - 2020-12-01

### Misc

- Ensure `pandoc` is installed to fix the Python release builds ([#24](https://github.com/swyddfa/esbonio/issues/24))

## v0.1.0 - 2020-12-01

### Features

- The language server can now offer completion suggestions for `directives` and
  `roles` ([#23](https://github.com/swyddfa/esbonio/issues/23))

## 0.0.6 - 2020-11-21

### Misc

- Add `--version` option to the cli that will print the version number and exit. ([#11](https://github.com/swyddfa/esbonio/issues/11))

## 0.0.5 - 2020-11-20

### Misc

- Update build pipeline to use `towncrier` to autogenerate release notes
  and changelog entries ([#5](https://github.com/swyddfa/esbonio/issues/5))
