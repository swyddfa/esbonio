.. _lsp-configuration:

Configuration
=============

Esbonio provides a flexible configuration system, allowing you to adapt the server to fit your project's needs.

Scopes & Sources
----------------

Configuration values are assigned one of the following scopes

- ``global``: For options that apply to the entire language server e.g. logging level.
- ``project``: For options that apply to a single project e.g. a ``sphinx-build`` command.

The language server supports reading configuration values from the following sources.

===================================  ==========================  =====
(Priortiy) Source                    Supported Scopes            Notes
===================================  ==========================  =====
\(1) ``initialzationOptions``        ``global``, ``project``     Settings for multiple projects are not supported.
\(2) :lsp:`workspace/configuration`  ``global``, ``project``
\(3) ``pyproject.toml`` files        ``project``
===================================  ==========================  =====

When determining the value to assign to a particular configuration option, Esbonio will merge options given by the sources in order of descending priority i.e. ``initializationOptions`` will override all other sources.

Options
-------

Below are all the configuration options supported by the server and their effects.

- :ref:`lsp-configuration-completion`
- :ref:`lsp-configuration-developer`
- :ref:`lsp-configuration-server`
- :ref:`lsp-configuration-sphinx`
- :ref:`lsp-configuration-preview`

.. _lsp-configuration-sphinx:

Sphinx
^^^^^^

The following options control the creation of the Sphinx application object managed by the server.

.. esbonio:config:: esbonio.sphinx.buildCommand
   :scope: project
   :type: string[]

   The ``sphinx-build`` command to use when invoking the Sphinx subprocess.

.. esbonio:config:: esbonio.sphinx.pythonCommand
   :scope: project
   :type: string[]

   The command to use when launching the Python interpreter for the process hosting the Sphinx application.
   Use this to select the Python environment you want to use when building your documentation.

.. esbonio:config:: esbonio.sphinx.cwd
   :scope: project
   :type: string

   The working directory from which to launch the Sphinx process.
   If not set, this will default to the root of the workspace folder containing the project.

.. esbonio:config:: esbonio.sphinx.envPassthrough
   :scope: project
   :type: string[]

   A list of environment variables to pass through to the Sphinx process.

.. esbonio:config:: sphinx.configOverrides
   :scope: project
   :type: object

   This option can be used to override values set in the project's ``conf.py`` file.
   This can be used to replace both the :option:`sphinx-build -D <sphinx:sphinx-build.-D>` and :option:`sphinx-build -A <sphinx:sphinx-build.-A>` cli options.

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

.. _lsp-configuration-preview:

Preview
^^^^^^^

The following options control the behavior of the preview

.. esbonio:config:: esbonio.sphinx.enableSyncScrolling
   :scope: project
   :type: boolean

   Enable support for syncronsied scrolling between the editor and preview pane

   .. note::

      In order to use syncronised scrolling, dedicated support for it needs to be implemented by your language client.
      See :ref:`lsp-feat-sync-scrolling` for details.

.. esbonio:config:: esbonio.preview.bind
   :scope: project
   :type: string

   The network interface to bind the preview server to.

.. esbonio:config:: esbonio.preview.httpPort
   :scope: project
   :type: integer

   The port number to bind the HTTP server to.
   If ``0``, a random port number will be chosen".

.. esbonio:config:: esbonio.preview.wsPort
   :scope: project
   :type: integer

   The port number to bind the WebSocket server to.
   If ``0``, a random port number will be chosen"

.. _lsp-configuration-server:

Server
^^^^^^

The following options control the behavior of the language server as a whole.

.. esbonio:config:: esbonio.server.logLevel
   :scope: global
   :type: string

   This can be used to set the level of log messages emitted by the server.
   This can be set to one of the following values.

   - ``error`` (default)
   - ``info``
   - ``debug``

.. esbonio:config:: esbonio.server.logFilter
   :scope: global
   :type: string[]

   The language server will typically include log output from all of its components.
   This option can be used to restrict the log output to be only those named.

.. _lsp-configuration-completion:

Completion
^^^^^^^^^^

The following options affect completion suggestions.

.. esbonio:config:: esbonio.server.completion.preferredInsertBehavior
   :scope: global
   :type: string

   Controls how completions behave when accepted, the following values are supported.

   - ``replace`` (default)

     Accepted completions will replace existing text, allowing the server to rewrite the current line in place.
     This allows the server to return all possible completions within the current context.
     In this mode the server will set the ``textEdit`` field of a ``CompletionItem``.

   - ``insert``

     Accepted completions will append to existing text rather than replacing it.
     Since rewriting is not possible, only the completions that are compatible with any existing text will be returned.
     In this mode the server will set the ``insertText`` field of a ``CompletionItem`` which should work better with editors that do no support ``textEdits``.

.. _lsp-configuration-developer:

Developer
^^^^^^^^^

The following options are useful when extending or working on the language server

.. esbonio:config:: esbonio.server.showDeprecationWarnings
   :scope: global
   :type: boolean

   Developer flag which, when enabled, the server will publish any deprecation warnings as diagnostics.

.. esbonio:config:: esbonio.server.enableDevTools (boolean)
   :scope: global
   :type: boolean

   Enable `lsp-devtools`_ integration for the language server itself.

.. esbonio:config:: esbonio.sphinx.enableDevTools (boolean)
   :scope: global
   :type: boolean

   Enable `lsp-devtools`_ integration for the Sphinx subprocess started by the language server.

.. esbonio:config:: esbonio.sphinx.pythonPath (string[])
   :scope: global
   :type: string[]

   List of paths to use when constructing the value of ``PYTHONPATH``.
   Used to inject the sphinx agent into the target environment."

.. _lsp-devtools: https://swyddfa.github.io/lsp-devtools/docs/latest/en/
