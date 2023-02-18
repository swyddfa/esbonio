v0.16.1 - 2023-02-18
--------------------

Fixes
^^^^^

- With live previews enabled, ``esbonio`` should no longer conflict with Sphinx extensions that register their own ``source-read`` handlers. (`#539 <https://github.com/swyddfa/esbonio/issues/539>`_)


v0.16.0 - 2023-02-04
--------------------

Features
^^^^^^^^

- Add new ``server.completion.preferredInsertBehavior`` option.
  This allows the user to indicate to the server how they would prefer completions to behave when accepted.

  The default value is ``replace`` and corresponds to the server's current behavior where completions replace existing text.
  In this mode the server will set the ``textEdit`` field of a ``CompletionItem``.

  This release also introduces a new mode ``insert``, where completions will append to existing text rather than replacing it.
  This also means that only the completions that are compatible with any existing text will be returned.
  In this mode the server will set the ``insertText`` field of a ``CompletionItem`` which should work better with editors that do no support ``textEdits``.

  **Note:** This option is only a hint and the server will not ensure that it is followed, though it is planned for all first party completion suggestions to (eventually) respect this setting.
  As of this release, all completion suggestions support ``replace``  and role, directive and directive option completions support ``insert``. (`#471 <https://github.com/swyddfa/esbonio/issues/471>`_)


Documentation
^^^^^^^^^^^^^

- Add getting started guide for Sublime Text by @vkhitrin (`#522 <https://github.com/swyddfa/esbonio/issues/522>`_)


API Changes
^^^^^^^^^^^

- ``CompletionContext`` objects now expose a ``config`` field that contains any user supplied configuration values affecting completions. (`#531 <https://github.com/swyddfa/esbonio/issues/531>`_)


Misc
^^^^

- Drop Python 3.6 support (`#400 <https://github.com/swyddfa/esbonio/issues/400>`_)
- Migrate to pygls ``v1.0``

  There are some breaking changes, but only if you use Esbonio's extension APIs, if you simply use the language server in your favourite editor you *shouldn't* notice a difference.

  The most notable change is the replacement of ``pydantic`` type definitions with ``attrs`` and ``cattrs`` via the new `lsprotocol <https://github.com/microsoft/lsprotocol>`__ package.
  For more details see pygls' `migration guide <https://pygls.readthedocs.io/en/latest/pages/migrating-to-v1.html>`__. (`#484 <https://github.com/swyddfa/esbonio/issues/484>`_)
- Drop support for Sphinx 3.x

  Add support for Sphinx 6.x (`#523 <https://github.com/swyddfa/esbonio/issues/523>`_)


v0.15.0 - 2022-12-03
--------------------

Features
^^^^^^^^

- Add initial support for synced scrolling and live previews of HTML builds.
  **Note** Both of these features rely on additional integrations outside of the LSP protocol therefore requiring dedicated support from clients.

  Synced scrolling support can be enabled by setting the ``server.enableScrollSync`` initialization option to ``True`` and works by injecting line numbers into the generated HTML which a client can use to align the preview window to the source window.

  Live preview support can be enabled by setting the ``server.enableLivePreview`` initialization option to ``True``, the language server will then pass the contents of unsaved files for Sphinx to build.
  Currently clients are responsible for triggering intermediate builds with the new ``esbonio.server.build`` command, though this requirement may be removed in future. (`#490 <https://github.com/swyddfa/esbonio/issues/490>`_)


Enhancements
^^^^^^^^^^^^

- Completion suggestions will now also be generated for the long form (``:py:func:``) of roles and directives in the primary and standard Sphinx domains. (`#416 <https://github.com/swyddfa/esbonio/issues/416>`_)
- The language server should now populate the ``serverInfo`` fields of its response to a client's ``initialize`` request. (`#497 <https://github.com/swyddfa/esbonio/issues/497>`_)
- The default ``suggest_options`` implementation for ``DirectiveLanguageFeatures`` should now be more useful in that it will return the keys from a directive's ``option_spec`` (`#498 <https://github.com/swyddfa/esbonio/issues/498>`_)
- The language server now recognises and returns ``DocumentLinks`` for ``image::`` and ``figure::`` directives that use ``http://`` or ``https://`` references for images. (`#506 <https://github.com/swyddfa/esbonio/issues/506>`_)


Fixes
^^^^^

- Fix handling of deprecation warnings in Python 3.11 (`#494 <https://github.com/swyddfa/esbonio/issues/494>`_)
- The language server should now correctly handle errors that occur while generating completion suggestions for a directive's options

  The language server should now show hovers for directives in the primary domain. (`#498 <https://github.com/swyddfa/esbonio/issues/498>`_)
- Errors thrown by ``DirectiveLanguageFeatures`` during ``textDocument/documentLink`` or ``textDocument/definition`` requests are now caught and no longer result in frustrating error banners in clients.

  The ``textDocument/documentLink`` handler for ``image::`` and ``figure::`` should no longer throw exceptions for invalid paths on Windows. (`#506 <https://github.com/swyddfa/esbonio/issues/506>`_)


API Changes
^^^^^^^^^^^

- ``RoleLanguageFeatures`` have been introduced as the preferred method of extending role support going forward.
  Subclasses can be implement any of the following methods

  - ``complete_targets`` called when generating role target completion items
  - ``find_target_definitions`` used to implement goto definition for role targets
  - ``get_implementation`` used to get the implementation of a role given its name
  - ``index_roles`` used to tell the language server which roles exist
  - ``resolve_target_link`` used to implement document links for role targets
  - ``suggest_roles`` called when generating role completion suggestions

  and are registered using the new ``Roles.add_feature()`` method. (`#495 <https://github.com/swyddfa/esbonio/issues/495>`_)


Deprecated
^^^^^^^^^^

- The following protocols have been deprecated and will be removed in ``v1.0``

  - ``TargetDefinition``
  - ``TargetCompletion``
  - ``TargetLink``

  The following methods have been deprecated and will be removed in ``v1.0``

  - ``Roles.add_target_definition_provider``
  - ``Roles.add_target_link_provider``
  - ``Roles.add_target_completion_provider``
  - ``RstLanguageServer.get_roles()``
  - ``SphinxLanguageServer.get_domain()``
  - ``SphinxLanguageServer.get_domains()``
  - ``SphinxLanguageServer.get_roles()``
  - ``SphinxLanguageServer.get_role_target_types()``
  - ``SphinxLanguageServer.get_role_targets()``
  - ``SphinxLanguageServer.get_intersphinx_targets()``
  - ``SphinxLanguageServer.has_intersphinx_targets()``
  - ``SphinxLanguageServer.get_intersphinx_projects()`` (`#495 <https://github.com/swyddfa/esbonio/issues/495>`_)


v0.14.3 - 2022-11-05
--------------------

Misc
^^^^

- Fix broken release pipeline (`#480 <https://github.com/swyddfa/esbonio/issues/480>`_)


v0.14.2 - 2022-11-05
--------------------

Enhancements
^^^^^^^^^^^^

- Add ``esbonio.server.showDeprecationWarnings`` option.

  This is flag is primarily aimed at developers working either directly on esbonio, or one of its extensions.
  When enabled, any warnings (such as ``DeprecationWarnings``) will be logged and published to the client as diagnostics. (`#443 <https://github.com/swyddfa/esbonio/issues/443>`_)


Fixes
^^^^^

- Spinx log messages are no longer duplicated after refreshing the application instance (`#460 <https://github.com/swyddfa/esbonio/issues/460>`_)


API Changes
^^^^^^^^^^^

- Added ``add_diagnostics`` method to the ``RstLanguageServer`` to enable adding diagnostics to a document incrementally. (`#443 <https://github.com/swyddfa/esbonio/issues/443>`_)
- The ``Directives`` language feature can now be extended by registering ``DirectiveLanguageFeatures`` using the new ``add_feature`` method.
  This is now the preferred extension mechanism and should be used by all extensions going forward. (`#444 <https://github.com/swyddfa/esbonio/issues/444>`_)
- ``DirectiveLanguageFeatures`` can now implement the following methods.

  - ``index_directives``: used to discover available directive implementations
  - ``suggest_directives``: used to determine which directive names can be suggested in the current completion context (``function`` vs ``py:function`` vs ``c:function`` etc.)
  - ``get_implementation``: used to go from a directive name (``function`` vs ``py:function``) to its implementation
  - ``suggest_options``: used to determine which directive options can be suggested in the current completion context (`#453 <https://github.com/swyddfa/esbonio/issues/453>`_)


Deprecated
^^^^^^^^^^

- ``ArgumentCompletion``, ``ArgumentDefinition`` and ``ArgumentLink`` directive providers have been deprecated in favour of ``DirectiveLanguageFeatures`` and will be removed in ``v1.0`` (`#444 <https://github.com/swyddfa/esbonio/issues/444>`_)
- Calling the ``get_directives()`` method on the ``RstLanguageServer`` and ``SphinxLanguageServer`` objects is deprecated in favour of calling the ``get_directives()`` method on the ``Directives`` language feature.
  It will be removed in ``v1.0``

  Calling the ``get_directive_options()`` method on the ``RstLanguageServer`` and ``SphinxLanguageServer`` objects deprecated and will be removed in ``v1.0``. (`#453 <https://github.com/swyddfa/esbonio/issues/453>`_)


Misc
^^^^

- Add Python 3.11 support (`#470 <https://github.com/swyddfa/esbonio/issues/470>`_)


v0.14.1 - 2022-09-11
--------------------

Fixes
^^^^^

- ``textDocument/documentSymbol`` requests should no longer fail on substitution definitions. (`#448 <https://github.com/swyddfa/esbonio/issues/448>`_)


v0.14.0 - 2022-07-31
--------------------

Features
^^^^^^^^

- The language server now supports ``textDocument/implementation`` requests for roles and directives. (`#431 <https://github.com/swyddfa/esbonio/issues/431>`_)


Enhancements
^^^^^^^^^^^^

- Line numbers for diagnostics for issues found within Python docstrings should now be more accurate. (`#433 <https://github.com/swyddfa/esbonio/issues/433>`_)
- Document symbol requests made for unsaved files now use the language client's version rather than the version on disk. (`#434 <https://github.com/swyddfa/esbonio/issues/434>`_)


Fixes
^^^^^

- Diagnostics for issues found in ``.. included::`` files should now have the correct filepath. (`#425 <https://github.com/swyddfa/esbonio/issues/425>`_)
- Extensions defined within Sphinx extensions or ``conf.py`` files can now take advantage of dependency injection (`#428 <https://github.com/swyddfa/esbonio/issues/428>`_)
- The server should now handle document symbol requests for files that are treated as reStructuredText files by a language client but don't have an ``*.rst`` extension. (`#434 <https://github.com/swyddfa/esbonio/issues/434>`_)


API Changes
^^^^^^^^^^^

- It is now possible to manually load an extension by calling the ``load_extension`` method on a language server object. (`#429 <https://github.com/swyddfa/esbonio/issues/429>`_)
- ``LanguageFeatures`` can now respond to ``textDocument/implementation`` requests by providing an ``implementation`` method and a collection of ``implementation_triggers``. (`#431 <https://github.com/swyddfa/esbonio/issues/431>`_)


v0.13.1 - 2022-06-29
--------------------

Fixes
^^^^^

- Log messages from Sphinx's startup are now captured and forwarded onto the language client. (`#408 <https://github.com/swyddfa/esbonio/issues/408>`_)
- Log messages from the server's startup are now captured and forwarded onto the language client. (`#417 <https://github.com/swyddfa/esbonio/issues/417>`_)
- Fixed handling of default roles when getting a document's initial doctree. (`#418 <https://github.com/swyddfa/esbonio/issues/418>`_)


API Changes
^^^^^^^^^^^

- Improved type annotations allow ``rst.get_feature`` to be called with a language feature's type and have the return type match accordingly. This should allow editors to provide better autocomplete suggestions etc. (`#409 <https://github.com/swyddfa/esbonio/issues/409>`_)
- ``esbonio_setup`` functions can now request specific language features and servers, just by providing type annotations e.g::

     from esbonio.lsp.roles import Roles
     from esbonio.lsp.sphinx import SphinxLanguageServer

     def esbonio_setup(rst: SphinxLanguageServer, roles: Roles):
         ...

  This function will then only be called when the language server is actually an instance of ``SphinxLanguageServer`` and only when that lanuage server instance contains an intance of the ``Roles`` feature. (`#410 <https://github.com/swyddfa/esbonio/issues/410>`_)


Deprecated
^^^^^^^^^^

- Calling ``rst.get_feature`` with a string will become an error in ``v.1.0``, a language feature's class should be given instead. (`#409 <https://github.com/swyddfa/esbonio/issues/409>`_)


v0.13.0 - 2022-05-27
--------------------

Features
^^^^^^^^

- Add initial ``textDocument/hover`` support, with documentation for roles and directives being shown.

  Add ``>`` to completion triggers. (`#311 <https://github.com/swyddfa/esbonio/issues/311>`_)


Fixes
^^^^^

- The language server now correctly handles diagnosics originating from ``.. c:function::`` directives. (`#393 <https://github.com/swyddfa/esbonio/issues/393>`_)


v0.12.0 - 2022-05-22
--------------------

Features
^^^^^^^^

- The language server now supports many (but not all) ``sphinx-build`` command line options.
  The ``sphinx.*`` section of the server's initialization options has been extened to include the following options.

  - ``configOverrides``
  - ``doctreeDir``
  - ``keepGoing``
  - ``makeMode``
  - ``quiet``
  - ``silent``
  - ``tags``
  - ``verbosity``
  - ``warningIsError``

  See the `documentation <https://swyddfa.github.io/esbonio/docs/latest/en/lsp/getting-started.html#configuration>`_ for details.

  Additionally, a new cli application ``esbonio-sphinx`` is now available which language clients (or users) can use to convert ``sphinx-build`` cli options to/from the server's initialization options. (`#360 <https://github.com/swyddfa/esbonio/issues/360>`_)


Enhancements
^^^^^^^^^^^^

- ``textDocument/documentSymbol`` responses now include symbol information on directives. (`#374 <https://github.com/swyddfa/esbonio/issues/374>`_)


Fixes
^^^^^

- ``.. include::`` directives no longer break goto definition for ``:ref:`` role targets (`#361 <https://github.com/swyddfa/esbonio/issues/361>`_)


API Changes
^^^^^^^^^^^

- Add method ``get_initial_doctree`` to ``RstLanguageServer`` which can be used to obtain a doctree of the given file before any role and directives have been applied. (`#374 <https://github.com/swyddfa/esbonio/issues/374>`_)


Misc
^^^^

- The ``esbonio.sphinx.numJobs`` configuration now defaults to ``1`` in line with ``sphinx-build`` defaults. (`#374 <https://github.com/swyddfa/esbonio/issues/374>`_)


v0.11.2 - 2022-05-09
--------------------

Enhancements
^^^^^^^^^^^^

- Add ``esbonio.lsp.rst._record`` and ``esbonio.lsp.sphinx._record`` startup modules.
  These can be used to record all LSP client-sever communication to a text file. (`#380 <https://github.com/swyddfa/esbonio/issues/380>`_)


Fixes
^^^^^

- The language server now detects functionality bundled with standard Sphinx extensions (`#381 <https://github.com/swyddfa/esbonio/issues/381>`_)


v0.11.1 - 2022-04-26
--------------------

Fixes
^^^^^

- ``textDocument/documentLink`` requests no longer fail when encountering `::` characters in C++ references. (`#377 <https://github.com/swyddfa/esbonio/issues/377>`_)


v0.11.0 - 2022-04-18
--------------------

Features
^^^^^^^^

- Add ``textDocument/documentLink`` support.

  The server supports resolving links for role targets with initial support for intersphinx references and local ``:doc:`` references.

  The server also supports resolving links for directive arguments with initial support for ``.. image::``, ``.. figure::``, ``.. include::`` and ``.. literalinclude::`` directives. (`#294 <https://github.com/swyddfa/esbonio/issues/294>`_)

Enhancements
^^^^^^^^^^^^

- Language clients can now control if the server forces a full build of a Sphinx project on startup by providing a ``sphinx.forceFullBuild`` initialization option, which defaults to ``true`` (`#358 <https://github.com/swyddfa/esbonio/issues/358>`_)
- Language clients can now control the number of parallel jobs by providing a ``sphinx.numJobs`` initialization option, which defaults to ``auto``. Clients can disable parallel builds by setting this option to ``1`` (`#359 <https://github.com/swyddfa/esbonio/issues/359>`_)

Fixes
^^^^^

- Goto definition for ``:ref:`` targets now works for labels containing ``-`` characters (`#357 <https://github.com/swyddfa/esbonio/issues/357>`_)
- Goto definition for ``:doc:`` targets will now only return a result if the referenced document actually exists. (`#369 <https://github.com/swyddfa/esbonio/issues/369>`_)


v0.10.3 - 2022-04-07
--------------------

Fixes
^^^^^

- A client's capabilities is now respected when constructing ``CompletionItems`` (`#270 <https://github.com/swyddfa/esbonio/issues/270>`_)
- Instead of spamming the client with notifications, the language server now reports Sphinx config/build errors as diagnostics. (`#315 <https://github.com/swyddfa/esbonio/issues/315>`_)
- Previews should now work on MacOS (`#341 <https://github.com/swyddfa/esbonio/issues/341>`_)
- Running ``$ esbonio`` directly on the command line now correctly starts the server again (`#346 <https://github.com/swyddfa/esbonio/issues/346>`_)
- The language server should no longer fail when suggesting completions for directives that are not class based.
  e.g. ``DirectiveContainer`` based directives from the ``breathe`` extension. (`#353 <https://github.com/swyddfa/esbonio/issues/353>`_)


v0.10.2 - 2022-03-22
--------------------

Fixes
^^^^^

- Previews on Windows should now start correctly (`#341 <https://github.com/swyddfa/esbonio/issues/341>`_)


v0.10.1 - 2022-03-20
--------------------

Fixes
^^^^^

- The language server should now correctly handle ``buildDir``, ``confDir`` and ``srcDir`` config values containing paths relative to ``~`` (`#342 <https://github.com/swyddfa/esbonio/issues/342>`_)


v0.10.0 - 2022-03-17
--------------------

Features
^^^^^^^^

- The server now provides an `esbonio.server.preview` command that can be used to preview HTML Sphinx projects via a local HTTP server. (`#275 <https://github.com/swyddfa/esbonio/issues/275>`_)
- The language server now accepts paths relative to ``${workspaceFolder}`` for Sphinx's ``confDir``, ``srcDir`` and ``builDir`` options. (`#304 <https://github.com/swyddfa/esbonio/issues/304>`_)
- The language server now supports ``textDocument/definition`` requests for ``.. image::`` directive arguments. (`#318 <https://github.com/swyddfa/esbonio/issues/318>`_)
- The language server now supports ``textDocument/definition`` requests for ``.. figure::`` directive arguments. (`#319 <https://github.com/swyddfa/esbonio/issues/319>`_)
- The language server will now look in sphinx extension modules and ``conf.py`` files for extensions to the language server. (`#331 <https://github.com/swyddfa/esbonio/issues/331>`_)


Fixes
^^^^^

- The language server no longer crashes when asked to ``--exclude`` a module that would not be loaded anyway. (`#313 <https://github.com/swyddfa/esbonio/issues/313>`_)
- Completion suggestions for domain objects referenced by roles such as ``:doc:``, ``:ref:``, ``:func:`` and many more now correctly update each time a rebuild is triggered. (`#317 <https://github.com/swyddfa/esbonio/issues/317>`_)
- Goto definition on a directive's arguments is no longer foiled by trailing whitespace. (`#327 <https://github.com/swyddfa/esbonio/issues/327>`_)


v0.9.0 - 2022-03-07
-------------------

Features
^^^^^^^^

- The language server now supports providing documentation on roles, directives (and their options).
  Note however, this requires the relevant documentation to be explicitly added to the relevant ``LanguageFeatures``. (`#36 <https://github.com/swyddfa/esbonio/issues/36>`_)
- The server now listens for ``workspace/didDeleteFiles`` notifications. (`#93 <https://github.com/swyddfa/esbonio/issues/93>`_)
- Add experimental spell checking support. (`#271 <https://github.com/swyddfa/esbonio/issues/271>`_)
- The language server now provides completion suggestions for ``.. code-block::`` and ``.. highlight::`` language names. (`#273 <https://github.com/swyddfa/esbonio/issues/273>`_)
- The language server now supports ``completionItem/resolve`` requests, it is currently implemented for roles, directives and directive options. (`#274 <https://github.com/swyddfa/esbonio/issues/274>`_)
- The language server now supports ``textDocument/definition`` requests for ``.. include::`` directive arguments. (`#276 <https://github.com/swyddfa/esbonio/issues/276>`_)
- The language server now supports ``textDocument/definition`` requests for ``.. literalinclude::`` directive arguments. (`#277 <https://github.com/swyddfa/esbonio/issues/277>`_)


Fixes
^^^^^

- Diagnostics are now cleared for deleted files. (`#291 <https://github.com/swyddfa/esbonio/issues/291>`_)


v0.8.0 - 2021-11-26
-------------------

Features
^^^^^^^^

- The language server now respects the project's ``default_role`` setting. (`#72 <https://github.com/swyddfa/esbonio/issues/72>`_)
- Initial implementation of the ``textDocument/documentSymbols`` request which for example, powers the "Outline" view in VSCode.
  Currently only section headers are returned. (`#242 <https://github.com/swyddfa/esbonio/issues/242>`_)
- The ``esbonio.sphinx.buildDir`` option now supports ``${workspaceRoot}`` and ``${confDir}`` variable expansions (`#259 <https://github.com/swyddfa/esbonio/issues/259>`_)


Fixes
^^^^^

- Role target ``CompletionItems`` now preserve additional cross reference modifiers like ``!`` and ``~`` (`#211 <https://github.com/swyddfa/esbonio/issues/211>`_)
- Intersphinx projects are now only suggested if they contain targets relevant to the current role. (`#244 <https://github.com/swyddfa/esbonio/issues/244>`_)
- Variables are now properly substituted in diagnostic messages. (`#246 <https://github.com/swyddfa/esbonio/issues/246>`_)


v0.7.0 - 2021-09-13
-------------------

Features
^^^^^^^^

- Add initial goto definition support.
  Currently only support definitions for ``:ref:`` and ``:doc:`` role targets. (`#209 <https://github.com/swyddfa/esbonio/issues/209>`_)


Fixes
^^^^^

- Completion suggestions for ``:option:`` targets now insert text in the correct format (``<progname> <option>``) (`#212 <https://github.com/swyddfa/esbonio/issues/212>`_)
- Diagnostics are now correctly cleared on Windows (`#213 <https://github.com/swyddfa/esbonio/issues/213>`_)
- Completion suggestions are no longer given in the middle of Python code. (`#215 <https://github.com/swyddfa/esbonio/issues/215>`_)
- ``CompletionItems`` should no longer corrupt existing text when selected. (`#223 <https://github.com/swyddfa/esbonio/issues/223>`_)


Misc
^^^^

- Updated ``pygls`` to ``v0.11.0`` (`#218 <https://github.com/swyddfa/esbonio/issues/218>`_)


v0.6.2 - 2021-06-05
-------------------

Fixes
^^^^^

- The language server now correctly handles windows file URIs when determining Sphinx's
  build directory. (`#184 <https://github.com/swyddfa/esbonio/issues/184>`_)
- Role and role target completions are now correctly generated when the role
  is being typed within parenthesis e.g. ``(:kbd:...`` (`#191 <https://github.com/swyddfa/esbonio/issues/191>`_)
- Path variables like ``${confDir}`` and ``${workspaceRoot}`` are now properly expanded
  even when there are no additional path elements. (`#208 <https://github.com/swyddfa/esbonio/issues/208>`_)


Misc
^^^^

- The cli arguments ``--cache-dir``, ``--log-filter``, ``--log-level`` and
  ``--hide-sphinx-output`` have been replaced with the configuration
  parameters ``esbonio.sphinx.buildDir``, ``esbonio.server.logFilter``,
  ``esbonio.logLevel`` and ``esbonio.server.hideSphinxOutput`` respectively (`#185 <https://github.com/swyddfa/esbonio/issues/185>`_)
- The language server's startup sequence has been reworked. Language clients are now
  required to provide configuration parameters under the ``initializationOptions`` field
  in the ``initialize`` request. (`#192 <https://github.com/swyddfa/esbonio/issues/192>`_)
- The language server will now send an `esbonio/buildComplete` notification to
  clients when it has finished (re)building the docs. (`#193 <https://github.com/swyddfa/esbonio/issues/193>`_)
- An entry for ``esbonio`` has been added to the ``console_scripts``
  entry point, so it's now possible to launch the language server by
  calling ``esbonio`` directly (`#195 <https://github.com/swyddfa/esbonio/issues/195>`_)


v0.6.1 - 2021-05-13
-------------------

Fixes
^^^^^

- Intersphinx projects are now only included as completion suggestions for roles
  which target object types in a project's inventory. (`#158 <https://github.com/swyddfa/esbonio/issues/158>`_)
- Fix the uri representation of Windows paths when reporting diagnostics (`#166 <https://github.com/swyddfa/esbonio/issues/166>`_)
- The language server now attempts to recreate the Sphinx application if the user
  updates a broken ``conf.py``. (`#169 <https://github.com/swyddfa/esbonio/issues/169>`_)
- The language server no longer crashes if clients don't send the ``esbonio.sphinx``
  configuration object (`#171 <https://github.com/swyddfa/esbonio/issues/171>`_)
- Docstrings from Sphinx and Docutils' base directive classes are no longer
  included in completion suggestions as they are not useful. (`#178 <https://github.com/swyddfa/esbonio/issues/178>`_)
- Sphinx build time exceptions are now caught and reported (`#179 <https://github.com/swyddfa/esbonio/issues/179>`_)
- Fix ``Method not found: $/setTrace`` exceptions when running against VSCode (`#180 <https://github.com/swyddfa/esbonio/issues/180>`_)


v0.6.0 - 2021-05-07
-------------------

Features
^^^^^^^^

- The Language Server will now offer filepath completions for the ``image``,
  ``figure``, ``include`` and ``literalinclude`` directives as well as the
  ``download`` role. (`#34 <https://github.com/swyddfa/esbonio/issues/34>`_)
- Language clients can now override the default ``conf.py`` discovery mechanism
  by providing a ``esbonio.sphinx.confDir`` config option. (`#62 <https://github.com/swyddfa/esbonio/issues/62>`_)
- Language clients can now override the assumption that Sphinx's ``srcdir``
  is the same as its ``confdir`` by providing a ``esbonio.sphinx.srcDir``
  config option. (`#142 <https://github.com/swyddfa/esbonio/issues/142>`_)


Fixes
^^^^^

- The Language Server no longer throws an exception while handling errors raised
  during initialization of a Sphinx application. (`#139 <https://github.com/swyddfa/esbonio/issues/139>`_)
- The Language Server now correctly offers completions for ``autoxxx`` directive options
  (`#100 <https://github.com/swyddfa/esbonio/issues/100>`_)


Misc
^^^^

- Upgrage pygls to v0.10.x (`#144 <https://github.com/swyddfa/esbonio/issues/144>`_)


v0.5.1 - 2021-04-20
-------------------

Fixes
^^^^^

- Pin ``pygls<0.10.0`` to ensure installs pick up a compatible version (`#147 <https://github.com/swyddfa/esbonio/issues/147>`_)


v0.5.0 - 2021-02-25
-------------------

Features
^^^^^^^^

- The language server now reports invalid references as diagnostics (`#57 <https://github.com/swyddfa/esbonio/issues/57>`_)
- Add ``--log-level`` cli argument that allows Language Clients to
  control the verbosity of the Language Server's log output. (`#87 <https://github.com/swyddfa/esbonio/issues/87>`_)
- Directive completions are now domain aware. (`#101 <https://github.com/swyddfa/esbonio/issues/101>`_)
- Role and role target completions are now domain aware. (`#104 <https://github.com/swyddfa/esbonio/issues/104>`_)
- Intersphinx completions are now domain aware (`#106 <https://github.com/swyddfa/esbonio/issues/106>`_)
- Add ``log-filter`` cli argument that allows Language Clients to choose
  which loggers they want to recieve messages from. Also add
  ``--hide-sphinx-output`` cli argument that can suppress Sphinx's build
  log as it it handled separately. (`#113 <https://github.com/swyddfa/esbonio/issues/113>`_)
- Add ``-p``, ``--port`` cli arguments that start the Language Server in
  TCP mode while specifying the port number to listen on. (`#114 <https://github.com/swyddfa/esbonio/issues/114>`_)
- Add ``--cache-dir`` cli argument that allows Language Clients to
  specify where cached data should be stored e.g. Sphinx's build output. (`#115 <https://github.com/swyddfa/esbonio/issues/115>`_)


Fixes
^^^^^

- The language server now reloads when the project's ``conf.py`` is modified (`#83 <https://github.com/swyddfa/esbonio/issues/83>`_)
- ``$/setTraceNotification`` notifications from VSCode no longer cause exceptions to be thrown
  in the Language Server. (`#91 <https://github.com/swyddfa/esbonio/issues/91>`_)
- Consistency errors are now included in reported diagnostics. (`#94 <https://github.com/swyddfa/esbonio/issues/94>`_)
- Ensure ``:doc:`` completions are specified relative to the project root. (`#102 <https://github.com/swyddfa/esbonio/issues/102>`_)


v0.4.0 - 2021-02-01
-------------------

Features
^^^^^^^^

- Directive option completions are now provided
  within a directive's options block (`#36 <https://github.com/swyddfa/esbonio/issues/36>`_)
- For projects that use ``interpshinx`` completions
  for intersphinx targets are now suggested when available (`#74 <https://github.com/swyddfa/esbonio/issues/74>`_)


Fixes
^^^^^

- Regex that catches diagnostics from Sphinx's
  output can now handle windows paths. Diagnostic reporting now sends a
  proper URI (`#66 <https://github.com/swyddfa/esbonio/issues/66>`_)
- Diagnostics are now reported on first startup (`#68 <https://github.com/swyddfa/esbonio/issues/68>`_)
- Fix exception that was thrown when trying to find
  completions for an unknown role type (`#73 <https://github.com/swyddfa/esbonio/issues/73>`_)
- The server will not offer completion suggestions outside of
  a role target (`#77 <https://github.com/swyddfa/esbonio/issues/77>`_)


v0.3.0 - 2021-01-27
-------------------

Features
^^^^^^^^

- Errors in Sphinx's build output are now parsed and published
  to the LSP client as diagnostics (`#35 <https://github.com/swyddfa/esbonio/issues/35>`_)
- Directive completions now include a snippet that
  prompts for any required arguments (`#58 <https://github.com/swyddfa/esbonio/issues/58>`_)


Fixes
^^^^^

- Errors encountered when initialising Sphinx are now caught and the language
  client is notified of an issue. (`#33 <https://github.com/swyddfa/esbonio/issues/33>`_)
- Fix issue where some malformed ``CompletionItem`` objects were
  preventing completion suggestions from being shown. (`#54 <https://github.com/swyddfa/esbonio/issues/54>`_)
- Windows paths are now handled correctly (`#60 <https://github.com/swyddfa/esbonio/issues/60>`_)
- Server no longer chooses ``conf.py`` files that
  are located under a ``.tox`` or ``site-packages`` directory (`#61 <https://github.com/swyddfa/esbonio/issues/61>`_)


v0.2.1 - 2020-12-08
-------------------

Fixes
^^^^^

- Directives that are part of the ``std`` or ``py`` Sphinx domains
  will now be included in completion suggestions (`#31 <https://github.com/swyddfa/esbonio/issues/31>`_)


v0.2.0 - 2020-12-06
-------------------

Features
^^^^^^^^

- Python log events can now published to Language Clients (`#27 <https://github.com/swyddfa/esbonio/issues/27>`_)
- Sphinx's build output is now redirected to the LSP client as log
  messages. (`#28 <https://github.com/swyddfa/esbonio/issues/28>`_)
- Suggest completions for targets for a number of roles from the
  `std <https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#the-standard-domain>`_
  and `py <https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#the-python-domain>`_
  domains including ``ref``, ``doc``, ``func``, ``meth``, ``class`` and more. (`#29 <https://github.com/swyddfa/esbonio/issues/29>`_)


Fixes
^^^^^

- Fix discovery of roles so that roles in Sphinx domains are used and
  that unimplemented ``docutils`` roles are not surfaced. (`#26 <https://github.com/swyddfa/esbonio/issues/26>`_)


v0.1.2 - 2020-12-01
-------------------

Misc
^^^^

- Use ``ubuntu-20.04`` for Python builds so that the correct version of ``pandoc`` is
  available (`#25 <https://github.com/swyddfa/esbonio/issues/25>`_)


v0.1.1 - 2020-12-01
-------------------

Misc
^^^^

- Ensure ``pandoc`` is installed to fix the Python release builds (`#24 <https://github.com/swyddfa/esbonio/issues/24>`_)


v0.1.0 - 2020-12-01
-------------------

Features
^^^^^^^^

- The language server can now offer completion suggestions for ``directives`` and
  ``roles`` (`#23 <https://github.com/swyddfa/esbonio/issues/23>`_)


0.0.6 - 2020-11-21
------------------

Misc
^^^^

- Add ``--version`` option to the cli that will print the version number and exit. (`#11 <https://github.com/swyddfa/esbonio/issues/11>`_)


0.0.5 - 2020-11-20
------------------

Misc
^^^^

- Update build pipeline to use ``towncrier`` to autogenerate release notes
  and changelog entries (`#5 <https://github.com/swyddfa/esbonio/issues/5>`_)
