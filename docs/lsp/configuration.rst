.. _lsp-configuration:

Configuration
=============

The language server provides the following configuration options

Sphinx
------

The following options control the creation of the Sphinx application object managed by the server.

.. confval:: esbonio.sphinx.buildCommand (string[])

   The ``sphinx-build`` command to use when invoking the Sphinx subprocess.

.. confval:: esbonio.sphinx.pythonCommand (string [])

   The command to use when launching the Python interpreter for the process hosting the Sphinx application.
   Use this to select the Python environment you want to use when building your documentation.

.. confval:: esbonio.sphinx.cwd (string)

   The working directory from which to launch the Sphinx process.
   If not set, this will default to the root of the workspace folder containing the project.

.. confval:: esbonio.sphinx.envPassthrough (string[])

   A list of environment variables to pass through to the Sphinx process.

.. confval:: sphinx.configOverrides (object)

   This option can be used to override values set in the project's ``conf.py`` file.
   This covers both the :option:`sphinx-build -D <sphinx:sphinx-build.-D>` and :option:`sphinx-build -A <sphinx:sphinx-build.-A>` cli options.

   For example the cli argument ``-Dlanguage=cy`` overrides a project's language, the equivalent setting using the ``configOverrides`` setting would be

   .. code-block:: json

      {
         "sphinx.configOverrides": {
            "language": "cy"
         }
      }

   Simiarly the argument ``-Adocstitle=ProjectName`` overrides the value of the ``docstitle`` variable inside HTML templates, the equivalent setting using ``configOverrides`` would be

   .. code-block:: json

      {
         "sphinx.configOverrides": {
            "html_context.docstitle": "ProjectName"
         }
      }

Preview
-------

The following options control the behavior of the preview

.. confval:: esbonio.sphinx.enableSyncScrolling (boolean)

   Enable support for syncronsied scrolling between the editor and preview pane

   .. note::

      In order to use syncronised scrolling, dedicated support for it needs to be implemented by your language client.
      See :ref:`lsp-feat-sync-scrolling` for details.

.. confval:: esbonio.preview.bind (string)

   The network interface to bind the preview server to.

.. confval:: esbonio.preview.httpPort (integer)

   The port number to bind the HTTP server to.
   If ``0``, a random port number will be chosen".

.. confval:: esbonio.preview.wsPort (integer)

   The port number to bind the WebSocket server to.
   If ``0``, a random port number will be chosen"

Server
------

The following options control the behavior of the language server as a whole.

.. confval:: esbonio.server.logLevel (string)

   This can be used to set the level of log messages emitted by the server.
   This can be set to one of the following values.

   - ``error`` (default)
   - ``info``
   - ``debug``

.. confval:: esbonio.server.logFilter (string[])

   The language server will typically include log output from all of its components.
   This option can be used to restrict the log output to be only those named.

Completion
----------

The following options affect completion suggestions.

.. confval:: esbonio.server.completion.preferredInsertBehavior (string)

   Controls how completions behave when accepted, the following values are supported.

   - ``replace`` (default)

     Accepted completions will replace existing text, allowing the server to rewrite the current line in place.
     This allows the server to return all possible completions within the current context.
     In this mode the server will set the ``textEdit`` field of a ``CompletionItem``.

   - ``insert``

     Accepted completions will append to existing text rather than replacing it.
     Since rewriting is not possible, only the completions that are compatible with any existing text will be returned.
     In this mode the server will set the ``insertText`` field of a ``CompletionItem`` which should work better with editors that do no support ``textEdits``.

Developer Options
------------------

The following options are useful when extending or working on the language server

.. confval:: esbonio.server.showDeprecationWarnings (boolean)

   Developer flag which, when enabled, the server will publish any deprecation warnings as diagnostics.

.. confval:: esbonio.server.enableDevTools (boolean)

   Enable `lsp-devtools`_ integration for the language server itself.

.. confval:: esbonio.sphinx.enableDevTools (boolean)

   Enable `lsp-devtools`_ integration for the Sphinx subprocess.

.. confval:: esbonio.sphinx.pythonPath (string[])

    List of paths to use when constructing the value of ``PYTHONPATH``.
    Used to inject the sphinx agent into the target environment."

.. _lsp-devtools: https://swyddfa.github.io/lsp-devtools/docs/latest/en/
