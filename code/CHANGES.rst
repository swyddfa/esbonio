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
