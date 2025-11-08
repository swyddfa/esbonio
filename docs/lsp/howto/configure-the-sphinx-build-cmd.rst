.. _lsp-configure-sphinx-build-cmd:

How To Configure the Sphinx Build Command
=========================================

.. highlight:: none

Unless told otherwise, ``esbonio`` will try to guess a sensible ``sphinx-build`` command that it will use when building your documentation.
This command will be adjusted to match your project's structure, but it will be something like the following::

  sphinx-build -M dirhtml docs ${defaultBuildDir}

where the ``${defaultBuildDir}`` variable expands into a subfolder of your user's cache directory, as determined by `platformdirs <https://platformdirs.readthedocs.io/en/latest/>`__.

Of course, the ``sphinx-build`` command you use with your project may be different from the default, in which case you can set the :esbonio:conf:`esbonio.sphinx.buildCommand` option in your project's ``pyproject.toml`` to override this.

.. code-block:: toml

   [tool.esbonio.sphinx]
   buildCommand = ["sphinx-build", "-M", "html", "docs", "${defaultBuildDir}", "--nitpicky", "--verbose"]

:esbonio:conf:`esbonio.sphinx.buildCommand` must be the genuine command line for ``sphinx-build``.
Wrapper scripts around ``sphinx-build``, e.g. a Makefile, are not supported.

.. admonition:: Why use ``${defaultBuildDir}``?

   There are two main reasons why ``esbonio`` will store its build output in your user's cache directory by default.

   #. There's no risk of ``esbonio`` accidentally clobbering files and folders in your project's structure.

   #. Esbonio's build output **is not the same** as the output produced by a standalone ``sphinx-build``.
      This is becasue ``esbonio``

      - Injects `custom HTML and JavaScript <https://github.com/swyddfa/esbonio/blob/develop/lib/esbonio/esbonio/sphinx_agent/static/webview.js>`__ in order to support its synchronised scrolling feature
      - Produces additional output files like the ``esbonio.db`` SQLite file that supports most of its LSP features.

Supported Options
-----------------

``esbonio`` supports *almost* every option supported by the :external+sphinx:std:doc:`man/sphinx-build` command.
The only exceptions are the options that do not make sense in the context of a language server, including

- ``--color`` / ``--no-color``, ``esbonio`` will always disable colors in the Sphinx processes it spawns
- ``-P`` / ``--pdb``, as there is no way for the user to interact with esbonio's background processes, there is no point launching a debugger when an exception is encountered.

Relative Filepaths
------------------

Filepaths like ``.`` or ``docs`` in a ``sphinx-build`` command obviously need to be resolved relative to some "current directory".
When using a ``pyproject.toml`` file, the current directory is set to the parent folder for example, say your project had the following structure::

  $ tree myproject
  myproject
   ├── docs
   │   └── conf.py
   └── pyproject.toml

Then your :esbonio:conf:`esbonio.sphinx.buildCommand` might look something like

.. code-block:: toml

   [tool.esbonio.sphinx]
   buildCommand = ["sphinx-build", "-M", "html", "docs", "${defaultBuildDir}"]

If you set the build command using the settings in your editor, the "current directory" will be set to root of your workspace

Config Overrides
----------------

Sphinx allows you to override options in your project's ``conf.py`` on the command line using the :external+sphinx:std:option:`-D <sphinx-build.-D>` or ``--define`` flags.
While you can provide these direct in your build command, ``esbonio`` offers a dedicated :esbonio:conf:`esbonio.sphinx.configOverrides` option where you can set these.

For example, to override the theme used by the project

.. code-block:: toml

   [tool.esbonio.sphinx]
   buildCommand = ["sphinx-build", "-M", "dirhtml", ".", "${defaultBuildDir}"]
   configOverrides = { html_theme = "alabaster" }

Though of course, this setting probably make most sense to be set via your editor.

HTML Overrides
--------------

Simiarly, using the :external+sphinx:std:option:`-A <sphinx-build.-A>` or ``--html-define`` flags you can override values that are passed to your HTML templates.
The :esbonio:conf:`esbonio.sphinx.configOverrides` option can also be used instead of these flags - provided that the values are nested inside a ``html_context`` "configuration option".

For example, there is a HTML template variable called ``docstitle`` that sets the title of the current page.
To override it to be ``My Custom Title`` you could use the following

.. code-block:: toml

   [tool.esbonio.sphinx]
   buildCommand = ["sphinx-build", "-M", "dirhtml", ".", "${defaultBuildDir}"]
   configOverrides = { html_context.docstitle = "My Custom Title" }

Though of course, this setting probably make most sense to be set via your editor.
