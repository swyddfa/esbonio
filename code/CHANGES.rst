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
