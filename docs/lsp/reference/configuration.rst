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
             "filename": "http.log",
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

The following options control the creation of the Sphinx application object managed by the server.

.. esbonio:config:: esbonio.sphinx.buildCommand
   :scope: project
   :type: string[]

   The ``sphinx-build`` command ``esbonio`` should use when building your documentation, for example::

     ["sphinx-build", "-M", "dirhtml", "docs", "${defaultBuildDir}", "--fail-on-warning"]

   This can contain any valid :external+sphinx:std:doc:`man/sphinx-build` argument however, the following arguments will be ignored and have no effect.

   - ``--color``, ``-P``, ``--pdb``

   Additionally, this option supports the following variables

   - ``${defaultBuildDir}``: Expands to esbonio's default choice of build directory

.. esbonio:config:: esbonio.sphinx.pythonCommand
   :scope: project
   :type: string[]

   Used to select the Python environment ``esbonio`` should use when building your documentation.
   This can be as simple as the full path to the Python executable in your virtual environment::

     ["/home/user/Projects/example/venv/bin/python"]

   Or a complex command with a number of options and arguments::

     ["hatch", "-e", "docs", "run", "python"]

   For more examples see :ref:`lsp-use-with`

.. esbonio:config:: esbonio.sphinx.cwd
   :scope: project
   :type: string

   The working directory from which to launch the Sphinx process.
   If not set

   - ``esbonio`` will use the directory containing the "closest" ``pyproject.toml`` file.
   - If no ``pyproject.toml`` file can be found, ``esbonio`` will use workspace folder containing the project.

.. esbonio:config:: esbonio.sphinx.envPassthrough
   :scope: project
   :type: string[]

   A list of environment variables to pass through to the Sphinx process.

.. esbonio:config:: esbonio.sphinx.configOverrides
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

.. esbonio:config:: esbonio.preview.bind
   :scope: project
   :type: string

   The network interface to bind the preview server to.

.. esbonio:config:: esbonio.preview.httpPort
   :scope: project
   :type: integer

   The port number to bind the HTTP server to.
   If ``0`` (the default), a random port number will be chosen

.. esbonio:config:: esbonio.preview.wsPort
   :scope: project
   :type: integer

   The port number to bind the WebSocket server to.
   If ``0`` (the default), a random port number will be chosen
