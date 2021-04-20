v0.5.1 - 2021-04-20v0.5.1 - 2021-04-20
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
