.. _lsp-cli:

Command Line Interface
======================

This page documents the command line interface provided by esbonio

``esbonio server``
------------------

The :program:`esbonio server` command launches the esbonio language server.

By default this start an instance of the language server configured to communicate over STDIO.

.. program:: esbonio server

.. option:: -p port, --port port

   When given this starts an instance of the language server configured to communicate over TCP on the given port number.

.. option:: -i module, --include module

   Add an additional module e.g. ``esbonio.server.features.sphinx_manager`` to the server configuration.
   To add multiple modules, this option can be given multiple times.

.. option:: -e module, --exclde module

   Exclude a module e.g. ``esbonio.server.features.sphinx_manager`` from the server configuration.
   To exclude multiple modules, this option can be given multiple times.

   .. note::

      Excluding a module will also automatically exclude any modules that depend on it

``esbonio sphinx``
------------------

Commands for interacting with Sphinx projects.
The following options apply to all commands under the ``esbonio sphinx`` namespace.

.. program:: esbonio sphinx

.. option:: -c PATH, --config PATH

   Read configuration values from the given path to a ``pyproject.toml`` file.
   If not given, commands will look for a ``pyproject.toml`` file in the current directory.

``esbonio sphinx build``
^^^^^^^^^^^^^^^^^^^^^^^^

The :program:`esbonio sphinx build` command builds a sphinx project

This command builds a sphinx project in the same manner as the esbonio language server,
meaning:

- Esbonio's additional sphinx extensions will be enabled
- Resulting html files will contain the HTML and JS necessary to support sync scrolling
- The ``esbonio.db`` file will be generated.

Useful as a debugging aid for compatibility issues.

In the absence of any additional command line flags, this command will look for a
pyproject.toml file in the current working directory and use the options in the
``[tool.esbonio.sphinx]`` section to configure the build.

If the pyproject.toml file is not found, or does not contain the relevant options
this command will attempt to derive a valid configuration, following the same
rules as the language server.

Providing additional command line flags will override this behaviour.

.. program:: esbonio sphinx build

.. option:: --build-args BUILD_ARGS

   Override the value of :esbonio:conf:`esbonio.sphinx.buildArguments`, arguments should be passed as a single quoted string e.g. ::

     $ esbonio sphinx build --build-args '-M dirhtml docs docs/_build'

   See :ref:`lsp-configure-sphinx-build-cmd` for more details.

.. option:: --python-cmd PYTHON_CMD

   Override the value of :esbonio:conf:`esbonio.sphinx.pythonCommand`, arguments should be passed as a single quoted string e.g. ::

     $ esbonio sphinx build --python-cmd 'uv run --with sphinx==9.1.0 python'

   See :ref:`lsp-configure-sphinx-build-env` for more details.

.. option:: --debug

   .. important::

      This option requires **both** ``esbonio`` and the target Sphinx environment to be using Python 3.14+

   Attach a pdb debugger to the build process.
