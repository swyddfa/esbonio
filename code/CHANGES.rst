v0.8.1 - 2022-03-22
-------------------

Fixes
^^^^^

- Fix handling of Windows URIs in preview code. (`#340 <https://github.com/swyddfa/esbonio/issues/340>`_)


v0.8.0 - 2022-03-17
-------------------

Features
^^^^^^^^

- Add commands ``esbonio.sphinx.selectConfDir``, ``esbonio.sphinx.selectSrcDir``, ``esbonio.sphinx.selectBuildDir``
  which allow the user to interactively select values for the ``esbonio.sphinx.confDir``, ``esbonio.sphinx.srcDir``, ``esbonio.sphinx.buildDir``
  options.

  The commands can be triggered through the command palette or the language status items. (`#337 <https://github.com/swyddfa/esbonio/issues/337>`_)


Fixes
^^^^^

- Language status items now correctly remove the errored status when an issue is resolved. (`#329 <https://github.com/swyddfa/esbonio/issues/329>`_)


Enhancements
^^^^^^^^^^^^

- Switched to an ``<iframe>`` based approach for previews, which should improve compatability with various Sphinx themes. (`#275 <https://github.com/swyddfa/esbonio/issues/275>`_)


Misc
^^^^

- Renamed the ``esbonio.server.entryPoint`` configuration option to ``esbonio.server.startupModule`` (`#337 <https://github.com/swyddfa/esbonio/issues/337>`_)


Removed
^^^^^^^

- The editor commands ``esbonio.insert.link`` and ``esbonio.insert.inlineLink`` have been removed.
  They are however available in the `reStructuredText <https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext>`_ extension. (`#307 <https://github.com/swyddfa/esbonio/issues/307>`_)


v0.7.3 - 2022-03-07
-------------------

Fixes
^^^^^

- Duplicate output channels are no longer created in the event of a language server crash. (`#287 <https://github.com/swyddfa/esbonio/issues/287>`_)
- Changes to ``esbonio.server.logLevel`` no longer require VSCode to be restarted to take effect client side. (`#301 <https://github.com/swyddfa/esbonio/issues/301>`_)
- Options such as ``esboino.server.logLevel`` can now be set on a per-project basis. (`#302 <https://github.com/swyddfa/esbonio/issues/302>`_)


Enhancements
^^^^^^^^^^^^

- The status bar has been re-implemented as a collection of language status items. (`#240 <https://github.com/swyddfa/esbonio/issues/240>`_)
- The server can now be restarted by clicking on the relevant language status item (`#241 <https://github.com/swyddfa/esbonio/issues/241>`_)
- Add option ``esbonio.server.enabledInPyFiles`` which allows the user to disable the language server in Python files. (`#285 <https://github.com/swyddfa/esbonio/issues/285>`_)
- All extension log output has been unified into a single output channel. (`#287 <https://github.com/swyddfa/esbonio/issues/287>`_)
- Add option ``esbonio.server.entryPoint`` which allows the user to set an entry point.
  Also add options ``esbonio.server.includedModules`` and ``esbonio.server.excludedModules`` to allow the user to control which modules are loaded in the server configuration. (`#288 <https://github.com/swyddfa/esbonio/issues/288>`_)
- The ``esbonio.server.pythonPath`` configuration option now supports paths relative to ``${workspaceRoot}`` (`#300 <https://github.com/swyddfa/esbonio/issues/300>`_)


Misc
^^^^

- Add soft dependency on `trond-snekvik.simple-rst <https://marketplace.visualstudio.com/items?itemName=trond-snekvik.simple-rst>`_ in favour of using bespoke grammar rules. (`#279 <https://github.com/swyddfa/esbonio/issues/279>`_)
- This extension now requires the Esbonio language server version to be ``>= 0.9.0`` (`#308 <https://github.com/swyddfa/esbonio/issues/308>`_)


v0.7.2 - 2021-11-26
-------------------

Fixes
^^^^^

- Simplified highlighting of footnote references to prevent edge cases from
  effectively disabling highlighting of a document. (`#252 <https://github.com/swyddfa/esbonio/issues/252>`_)
- Literal block markers no longer disable highlighting of any preceeding content. (`#254 <https://github.com/swyddfa/esbonio/issues/254>`_)
- Code blocks that have injected grammars (e.g. python code blocks) now correctly highlight any options
  on the directive (`#255 <https://github.com/swyddfa/esbonio/issues/255>`_)


Enhancements
^^^^^^^^^^^^

- Add ``esbonio.server.enabled`` option which gives the user the ability to disable the language sever if they wish. (`#239 <https://github.com/swyddfa/esbonio/issues/239>`_)
- Code blocks that contain a language that's not recognised, are now highlighted as strings. (`#253 <https://github.com/swyddfa/esbonio/issues/253>`_)
- Add ``esbonio.sphinx.buildDir`` option which allows the user to specify where Sphinx's build files get written to. (`#258 <https://github.com/swyddfa/esbonio/issues/258>`_)


v0.7.1 - 2021-09-13
-------------------

Fixes
^^^^^

- Fix handling of ``<script>`` tags without a ``src`` attribute when generating the
  HTML preview of a page. (`#214 <https://github.com/swyddfa/esbonio/issues/214>`_)


Enhancements
^^^^^^^^^^^^

- When the user is using an environment with an incompatible Python version but have
  the Python extension available, they are given the option of picking a new environment to use. (`#176 <https://github.com/swyddfa/esbonio/issues/176>`_)
- When the user is prompted to install the language server in the current environment,
  they now also have the option of picking a new environment to use instead. (`#224 <https://github.com/swyddfa/esbonio/issues/224>`_)


Misc
^^^^

- This extension does not support untrusted workspaces. (`#217 <https://github.com/swyddfa/esbonio/issues/217>`_)


v0.7.0 - 2021-06-05
-------------------

Features
^^^^^^^^

- Add the ability to preview the output from the ``html`` builder.` (`#190 <https://github.com/swyddfa/esbonio/issues/190>`_)
- Add a statusbar item that indicates the state of the language server. (`#194 <https://github.com/swyddfa/esbonio/issues/194>`_)
- VSCode will now syntax highlight C, C++, Javascript and Typescript code blocks (`#205 <https://github.com/swyddfa/esbonio/issues/205>`_)


Fixes
^^^^^

- Fix incorrect syntax highlighting of multiple links on a single line (`#203 <https://github.com/swyddfa/esbonio/issues/203>`_)
- VSCode now treats ``*`` characters as quotes, meaning selecting some text and entering
  a ``*`` will automatically surround that text rather than replacing it. (`#204 <https://github.com/swyddfa/esbonio/issues/204>`_)


Misc
^^^^

- The cli arguments ``--cache-dir``, ``--log-filter``, ``--log-level`` and
  ``--hide-sphinx-output`` have been replaced with the configuration
  parameters ``esbonio.sphinx.buildDir``, ``esbonio.server.logFilter``,
  ``esbonio.logLevel`` and ``esbonio.server.hideSphinxOutput`` respectively (`#185 <https://github.com/swyddfa/esbonio/issues/185>`_)
- The language server's startup sequence has been reworked. Language clients are now
  required to provide configuration parameters under the ``initializationOptions`` field
  in the ``initialize`` request. (`#192 <https://github.com/swyddfa/esbonio/issues/192>`_)


v0.6.2 - 2021-05-14
-------------------

Fixes
^^^^^

- Fix minimum required language server version (`#183 <https://github.com/swyddfa/esbonio/issues/183>`_)


v0.6.1 - 2021-05-13
-------------------

Fixes
^^^^^

- Literal blocks now have the correct syntax highlighting (`#138 <https://github.com/swyddfa/esbonio/issues/138>`_)
- The language server is now reloaded when the Python environment is changed. (`#140 <https://github.com/swyddfa/esbonio/issues/140>`_)
- It's now possible to test dev builds of the language server with the extension (`#168 <https://github.com/swyddfa/esbonio/issues/168>`_)


Misc
^^^^

- Improvements to the development experience (`#170 <https://github.com/swyddfa/esbonio/issues/170>`_)


v0.6.0 - 2021-05-07
-------------------

Features
^^^^^^^^

- Add new ``esbonio.sphinx.confDir`` option that allows for a project's config
  directory to be explictly set should the automatic discovery in the Language
  Server fail. (`#63 <https://github.com/swyddfa/esbonio/issues/63>`_)
- Add new ``esbonio.sphinx.srcDir`` option that allows for overriding the
  language server's assumption that source files are located in the same
  place as the ``conf.py`` file. (`#142 <https://github.com/swyddfa/esbonio/issues/142>`_)


Fixes
^^^^^

- Editor keybindings now only apply in ``*.rst`` files. (`#141 <https://github.com/swyddfa/esbonio/issues/141>`_)


Misc
^^^^

- Update ``vscode-languageclient`` to v7.0.0 (`#152 <https://github.com/swyddfa/esbonio/issues/152>`_)


v0.5.1 - 2021-03-01
-------------------

Misc
^^^^

- Fix release pipeline (`#135 <https://github.com/swyddfa/esbonio/issues/135>`_)


v0.5.0 - 2021-03-01
-------------------

Features
^^^^^^^^

- Add new ``esbonio.server.installBehavior`` option that gives greater control
  over how Language Server installation is handled. ``automatic`` will install the
  server in new environments without prompting, ``prompt`` will ask for
  confirmation first and ``nothing`` disables installation entirely.` (`#92 <https://github.com/swyddfa/esbonio/issues/92>`_)
- Expose ``esbonio.server.logFilter`` option that can be used to limit the
  components of the language server which produce output. (`#118 <https://github.com/swyddfa/esbonio/issues/118>`_)
- Expose ``esbonio.server.hideSphinxOutput`` option which allows for Sphinx's
  build output to be omitted from the log. (`#120 <https://github.com/swyddfa/esbonio/issues/120>`_)
- The extension will now automatically restart the Language Server when the
  extension's configuration is updated (`#122 <https://github.com/swyddfa/esbonio/issues/122>`_)
- ``css``, ``html``, ``json`` and ``yaml`` code blocks are now syntax highlighted. (`#125 <https://github.com/swyddfa/esbonio/issues/125>`_)


Fixes
^^^^^

- The extension now checks that the configured Python verison is compatible with
  the Language Server. (`#97 <https://github.com/swyddfa/esbonio/issues/97>`_)
- Fix syntax higlighting for namespaced roles (e.g. ``:py:func:``) and directives
  (e.g. ``.. py:function::``) (`#98 <https://github.com/swyddfa/esbonio/issues/98>`_)
- Invalid literals are no longer highlighted as valid syntax (`#99 <https://github.com/swyddfa/esbonio/issues/99>`_)
- Ensure that the Language Server uses the latest config options when restarted (`#121 <https://github.com/swyddfa/esbonio/issues/121>`_)
- The extension now enforces a minimum Language Server version (`#123 <https://github.com/swyddfa/esbonio/issues/123>`_)
- Fixed syntax highlighting of footnotes. (`#124 <https://github.com/swyddfa/esbonio/issues/124>`_)
- Fix syntax highlighting where sentences containing ellipses were incorrectly
  identified as a comment (`#126 <https://github.com/swyddfa/esbonio/issues/126>`_)
- Invalid bold text (e.g. ``** invalid**``) is no longer highlighted as valid
  syntax. (`#127 <https://github.com/swyddfa/esbonio/issues/127>`_)
- Invalid italic text (e.g. ``*invalid *``) is no longer highlighted as valid
  syntax. (`#128 <https://github.com/swyddfa/esbonio/issues/128>`_)


Misc
^^^^

- The language server's logging level is set to match the logging level defined in
  the extension. (`#86 <https://github.com/swyddfa/esbonio/issues/86>`_)
- The extension now makes use of the ``--cache-dir`` cli option in the language
  server to set Sphinx's build output to use a known location. (`#119 <https://github.com/swyddfa/esbonio/issues/119>`_)
- If ``esbonio.server.logLevel`` is set to ``debug`` the extension assumes the
  user is working on the Language Server and will automatically open the log panel
  on restarts. (`#133 <https://github.com/swyddfa/esbonio/issues/133>`_)


v0.4.0 - 2021-02-03
-------------------

Features
^^^^^^^^

- Expose an ``esbonio.log.level`` config option that allows the level of logging
  output to be configured (`#85 <https://github.com/swyddfa/esbonio/issues/85>`_)
- Add ``esbonio.server.updateFrequency`` option that controls how often the
  extension should check for updates. Valid values are ``daily``, ``weekly``,
  ``monthly`` and ``never``` (`#88 <https://github.com/swyddfa/esbonio/issues/88>`_)
- Add ``esbonio.server.updateBehavior`` option that controls how updates should be
  applied. Valid values are ``promptAlways``, ``promptMajor`` and ``automatic`` (`#89 <https://github.com/swyddfa/esbonio/issues/89>`_)


Fixes
^^^^^

- Fix edge cases around syntax highlighting bold/italic elements. (`#47 <https://github.com/swyddfa/esbonio/issues/47>`_)
- The extension now activates when it detects a sphinx project (`#49 <https://github.com/swyddfa/esbonio/issues/49>`_)
- The language client now also listens to changes in Python files so that we can
  pick up changes in the project's ``conf.py``` (`#50 <https://github.com/swyddfa/esbonio/issues/50>`_)
- Fix edge cases around syntax highlighting inline code snippets (`#70 <https://github.com/swyddfa/esbonio/issues/70>`_)


v0.3.1 - 2020-12-14
-------------------

Misc
^^^^

- Fix ``vsix`` packaging so that grammar tests are not included. (`#44 <https://github.com/swyddfa/esbonio/issues/44>`_)


v0.3.0 - 2020-12-14
-------------------

Features
^^^^^^^^

- Add 2 commands that can be used to insert links. One that uses the inline syntax
  :kbd:`Alt+L`, the other, the named reference syntax :kbd:`Alt+Shift+L` (`#37 <https://github.com/swyddfa/esbonio/issues/37>`_)
- Add command that will restart the language server (`#39 <https://github.com/swyddfa/esbonio/issues/39>`_)


Fixes
^^^^^

- Support syntax highligting for more header styles. Support highligting python code
  under directives from Sphinx's ``sphinx.ext.doctest`` extension (`#42 <https://github.com/swyddfa/esbonio/issues/42>`_)


v0.2.1 - 2020-11-28
-------------------

Misc
^^^^

- The published ``vsix`` now contains a changelog in a format that's compatible with the
  VSCode marketplace. (`#16 <https://github.com/swyddfa/esbonio/issues/16>`_)
- The published ``vsix`` package now only contains the files that are necessary. (`#17 <https://github.com/swyddfa/esbonio/issues/17>`_)
- The extension is now bundled into a single file using webpack (`#18 <https://github.com/swyddfa/esbonio/issues/18>`_)


v0.2.0 - 2020-11-27
-------------------

Features
^^^^^^^^

- If there is no Python interpreter configured and the
  `Python extension <https://marketplace.visualstudio.com/items?itemName=ms-python.python>`_
  is available, then esbonio will now use the interpreter that's been configured for the
  Python extension (`#9 <https://github.com/swyddfa/esbonio/issues/9>`_)


v0.1.0 - 2020-11-23
-------------------

Features
^^^^^^^^

- If the language server is not installed, the extension will now prompt to install it.
  It will also prompt to update it when new versions are available. (`#12 <https://github.com/swyddfa/esbonio/issues/12>`_)


Misc
^^^^

- Update build pipeline to use ``towncrier`` to autogenerate release notes and changelog
  entries (`#10 <https://github.com/swyddfa/esbonio/issues/10>`_)
