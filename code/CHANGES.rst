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
