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
\(1) :lsp:`workspace/configuration`  ``global``, ``project``
\(2) ``pyproject.toml`` files        ``project``
\(3) ``initialzationOptions``        ``global``, ``project``     Settings for multiple projects are not supported.
===================================  ==========================  =====

When determining the value to assign to a particular configuration option, Esbonio will merge options given by the sources in order of descending priority i.e. options set via :lsp:`workspace/configuration` requests will override all other sources.

Options
-------

Below are all the configuration options supported by the server and their effects.

- :ref:`lsp-configuration-completion`
- :ref:`lsp-configuration-developer`
- :ref:`lsp-configuration-logging`
- :ref:`lsp-configuration-sphinx`
- :ref:`lsp-configuration-preview`

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

.. esbonio:config:: esbonio.server.enableDevTools
   :scope: global
   :type: boolean

   Enable `lsp-devtools`_ integration for the language server itself.

.. esbonio:config:: esbonio.sphinx.enableDevTools
   :scope: global
   :type: boolean

   Enable `lsp-devtools`_ integration for the Sphinx subprocess started by the language server.

.. esbonio:config:: esbonio.sphinx.pythonPath
   :scope: global
   :type: string[]

   List of paths to use when constructing the value of ``PYTHONPATH``.
   Used to inject the sphinx agent into the target environment."

.. esbonio:config:: esbonio.preview.showLineMarkers
   :scope: global
   :type: boolean

   When enabled, reveal the source uri and line number (if possible) for the html element under the cursor.

.. _lsp-devtools: https://swyddfa.github.io/lsp-devtools/docs/latest/en/

.. _lsp-configuration-logging:

Logging
^^^^^^^

The following options control the logging output of the language server.

.. esbonio:config:: esbonio.logging.level
   :scope: global
   :type: string

   Sets the default level of log messages emitted by the server.
   The following values are accepted, sorted in the order from least to most verbose.

   - ``critical``
   - ``fatal``
   - ``error`` (default)
   - ``warning``
   - ``info``
   - ``debug``

.. esbonio:config:: esbonio.logging.format
   :scope: global
   :type: string

   Sets the default format string to apply to log messages.
   This can be any valid :external:ref:`%-style <old-string-formatting>` format string, referencing valid :external:ref:`logrecord-attributes`

   **Default value:** ``[%(name)s]: %(message)s``

.. esbonio:config:: esbonio.logging.filepath
   :scope: global
   :type: string

   If set, record log messages in the given filepath (relative to the server's working directory)

.. esbonio:config:: esbonio.logging.stderr
   :scope: global
   :type: boolean

   If ``True`` (the default), the server will print log messages to the process' stderr

.. esbonio:config:: esbonio.logging.window
   :scope: global
   :type: boolean

   If ``True``, the server will send messages to the client as :lsp:`window/logMessage` notifications

.. esbonio:config:: esbonio.logging.config
   :scope: global
   :type: object

   This is an object used to override the default logging configuration for specific, named loggers.
   Keys in the object are the names of loggers to override, values are a dictionary that can contain the following fields

   - ``level`` if present, overrides the value of :esbonio:conf:`esbonio.logging.level`
   - ``format`` if present, overrides the value of :esbonio:conf:`esbonio.logging.format`
   - ``filepath`` if present, overrides the value of :esbonio:conf:`esbonio.logging.filepath`
   - ``stderr`` if present, overrides the value of :esbonio:conf:`esbonio.logging.stderr`
   - ``window`` if present, overrides the value of :esbonio:conf:`esbonio.logging.window`

Examples
""""""""

.. highlight:: json

The following is equivalent to the server's default logging configuration::

   {
     "esbonio": {
       "logging": {
         "level": "error",
         "format": "[%(name)s]: %(message)s",
         "stderr": true,
         "config": {
           "sphinx": {
             "level": "info",
             "format": "%(message)s"
           }
         }
       }
     }
   }

This sets the default log level to ``debug`` and dials back or redirects the output from some of the noisier loggers::

   {
     "esbonio": {
       "logging": {
         "level": "debug",
         "config": {
           "esbonio.Configuration": {
             "level": "info"
           },
           "esbonio.PreviewServer": {
             "filepath": "http.log",
             "stderr": false
           },
           "esbonio.WebviewServer": {
             "level": "error"
           }
         }
       }
     }
   }

Loggers
"""""""

The following table summarises (some of) the available loggers and the type of messages they report

==========================  ===========
Name                        Description
==========================  ===========
``esbonio``                 Messages coming from ``esbonio`` itself that do not belong anywhere else
``esbonio.Configuration``   Messages about merging configuration from multiple sources and notifying the rest of the server when values change.
``esbonio.PreviewManager``  Messages from the component orchestrating the HTTP and Websocket servers that power the preview functionality
``esbonio.PreviewServer``   Records the HTTP traffic from the server that serves the HTML files built by Sphinx
``esbonio.SphinxManager``   Messages from the component that manages the server's underlying Sphinx processes
``esbonio.WebviewServer``   Messages about the websocket connection between the HTML viewer and the server
``py.warnings``             Log messages coming from Python's warnings framework
``sphinx``                  Log messages coming from an underlying sphinx process
==========================  ===========

.. _lsp-configuration-sphinx:

Sphinx
^^^^^^

The following options control the creation and management of background Sphinx process used by the server

.. tab-set::

   .. tab-item:: pyproject.toml
      :sync: pyproject

      .. code-block:: toml

         [tool.esbonio.sphinx]
         buildCommand = ["sphinx-build", "-M", "dirhtml", "docs", "docs/_build"]
         configOverrides = { html_theme = "alabaster", language = "cy" }
         pythonCommand = ["uv", "run", "python"]

         # Alternatively for more control over how the background Sphinx process is launched.
         #
         # [tool.esbonio.sphinx.pythonCommand]
         # command = ["hatch", "-e", "docs", "run", "python"]
         # cwd = "${scopeFsPath}/docs"
         # env = {MYENVVAR = "value"}

   .. tab-item:: settings.json (VSCode only)
      :sync: vscode

      .. code-block:: json

         {
           "esbonio.sphinx.buildCommand": [
              "sphinx-build", "-M", "dirhtml", "docs", "docs/_build"
           ],
           "esbonio.sphinx.configOverrides": {
               "html_theme": "alabaster",
               "language": "cy",
           },
           "esbonio.sphinx.pythonCommand": {
              "command": ["uv", "run", "python"],
              "cwd": "${scopeFsPath}",
              "env": {
                  "MYENVVAR": "value"
              }
           }

           "esbonio.sphinx.buildTriggers": { "onSave": true, "onChange": 2.0 }
         }

.. esbonio:config:: esbonio.sphinx.buildCommand
   :scope: project
   :type: string[]

   The ``sphinx-build`` command ``esbonio`` should use when building your documentation
   For more information, see :ref:`lsp-configure-sphinx-build-cmd`

.. esbonio:config:: esbonio.sphinx.configOverrides
   :scope: project
   :type: object

   This option can be used to override values set in the project's ``conf.py`` file.
   This can be used to replace both the :option:`sphinx-build -D <sphinx:sphinx-build.-D>` and :option:`sphinx-build -A <sphinx:sphinx-build.-A>` cli options.

   See :ref:`lsp-configure-sphinx-build-cmd` for details

.. esbonio:config:: esbonio.sphinx.pythonCommand
   :scope: project
   :type: string[]

   Instructs ``esbonio`` how to launch the Python interpreter it uses for the background Sphinx process.
   Use this option to ensure that the correct Python environment for your documentation is selected.

   This can be as simple as the full path to the Python executable in your virtual environment::

     ["/home/user/Projects/example/venv/bin/python"]

   Or a complex command with a number of options and arguments::

     ["hatch", "-e", "docs", "run", "python"]

   If the command is not ``python``, then it must accept additional parameters (e.g. ``-M sphinx``) and pass these to the Python interpreter.
   The command must not replace or clear the environment variable ``PYTHONPATH``, it may, however, extend it with additional entries.

   For more examples see :ref:`lsp-configure-sphinx-build-env`

.. esbonio:config:: esbonio.sphinx.pythonCommand.cwd
   :scope: project
   :type: string

   The working directory from which to launch the Sphinx process.
   If not set

   - ``esbonio`` will use the directory containing the closest ``pyproject.toml`` file.
   - If no ``pyproject.toml`` file can be found, ``esbonio`` will use workspace folder containing the project.

.. esbonio:config:: esbonio.sphinx.pythonCommand.env
   :scope: project
   :type: object

   Additional environment variables to set for the background Sphinx process

.. esbonio:config:: esbonio.sphinx.buildTriggers
   :scope: global
   :type: object

   This option controls when the language server rebuilds your documentation.
   The server's default configuration is equivalent to setting

   .. tab-set::

      .. tab-item:: VSCode

         .. code-block:: json

            {
              "esbonio.sphinx.buildTriggers": {
                "onSave": true,
                "onChange": 2.0,
              }
            }

   where ``esbonio`` will rebuild each time you save a file, or each time you modify a file after a delay of 2 seconds.

   The following configuration will disable **all** builds

   .. code-block:: json

      {
        "esbonio.sphinx.buildTriggers": {
          "onSave": false,
          "onChange": false,
        }
      }

.. _lsp-configuration-preview:

Preview
^^^^^^^

The following options control the behavior of the HTML preview

.. tab-set::

   .. tab-item:: settings.json (VSCode only)

      .. code-block:: json

         {
             "esbonio.preview.bind": "localhost",
             "esbonio.preview.httpPort": 1234,
             "esbonio.preview.wsPort": 0,
             "esbonio.preview.synchronizeScroll": "bothWays",
         }

.. esbonio:config:: esbonio.preview.bind
   :scope: global
   :type: string

   The network interface to bind the preview server to.

.. esbonio:config:: esbonio.preview.httpPort
   :scope: global
   :type: integer

   The port number to bind the HTTP server to.
   If ``0`` (the default), a random port number will be chosen

.. esbonio:config:: esbonio.preview.wsPort
   :scope: global
   :type: integer

   The port number to bind the WebSocket server to.
   If ``0`` (the default), a random port number will be chosen

.. esbonio:config:: esbonio.preview.synchronizeScroll
   :scope: global
   :type: string

   Controls how synchronized scrolling behaves.
   The valid options are

   - ``bothWays`` (default): Scrolling in either the editor or preview window will update the other window
   - ``editorWithPreview``: Scrolling the editor window will update the preview window, but not vice-versa
   - ``previewWithEditor``: Scrolling the preview window will update the editor window, but not vice-versa
   - ``disabled``: Disable any form of synchronized scrolling
