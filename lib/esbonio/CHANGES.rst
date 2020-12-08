v0.2.1 - 2020-12-08
-------------------

Fixes
^^^^^

- **Language Server** Directives that are part of the ``std`` or ``py`` Sphinx domains
  will now be included in completion suggestions (`#31 <https://github.com/swyddfa/esbonio/issues/31>`_)


v0.2.0 - 2020-12-06
-------------------

Features
^^^^^^^^

- **Language Server:** Python log events can now published to Language Clients (`#27 <https://github.com/swyddfa/esbonio/issues/27>`_)
- **Language Server** Sphinx's build output is now redirected to the LSP client as log
  messages. (`#28 <https://github.com/swyddfa/esbonio/issues/28>`_)
- **Language Server** Suggest completions for targets for a number of roles from the
  `std <https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#the-standard-domain>`_
  and `py <https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#the-python-domain>`_
  domains including ``ref``, ``doc``, ``func``, ``meth``, ``class`` and more. (`#29 <https://github.com/swyddfa/esbonio/issues/29>`_)


Fixes
^^^^^

- **Language Server:** Fix discovery of roles so that roles in Sphinx domains are used and
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
