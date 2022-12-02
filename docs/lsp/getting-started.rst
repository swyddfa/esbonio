.. _lsp_getting_started:

Getting Started
===============

This section contains notes on how to use the language server with your text editor of choice.

.. admonition:: Don't see your favourite editor?

   Feel free to submit a pull request with steps on how to get started or if you're not
   sure on where to start, `open an issue`_ and we'll help you figure it out.

.. relevant-to:: Editor

   VSCode (Esbonio)
      .. figure:: /images/vscode-screenshot.png
         :align: center
         :target: /_images/vscode-screenshot.png

         The Esbonio VSCode extension.

   Emacs (eglot)
      .. figure:: /images/emacs-eglot-extended.png
         :align: center
         :target: /_images/emacs-eglot-extended.png

         Emacs, Esbonio and the ``eglot-extended.el`` configuration

   Emacs (lsp-mode)
      .. figure:: /images/emacs-lsp-mode-extended.png
         :align: center
         :target: /_images/emacs-lsp-mode-extended.png

         Emacs, Esbonio and the ``lsp-mode-extended.el`` configuration

   Kate
      .. figure:: /images/kate-screenshot.png
         :align: center
         :target: /_images/kate-screenshot.png

         Using the Esbonio language server within Kate.

      `Kate <https://kate-editor.org/en-gb/>`_ is a text editor from the KDE project and comes with LSP support.

   Neovim (lspconfig)
      .. figure:: /images/nvim-lspconfig.png
         :align: center
         :target: /_images/nvim-lspconfig.png

         Using Esbonio with Neovim's built-in language client.

   Vim (coc.nvim)
      .. figure:: /images/nvim-coc.png
         :align: center
         :target: /_images/nvim-coc.png

         Using Esbonio in Neovim via ``coc.nvim`` and the ``coc-esbonio`` extension.

   Vim (vim-lsp)
      .. figure:: /images/nvim-vim-lsp.png
         :align: center
         :target: /_images/nvim-vim-lsp.png

         Using Esbonio and Neovim with ``vim-lsp``

Installation
------------

The language server can be installed using pip

.. code-block:: console

   $ pip install esbonio

Sphinx and the reStructuredText format itself are highly extensible so the available
features can differ greatly from project to project. For this reason the
language server should be installed into the same environment you use when
building your documentation e.g.

.. code-block:: console

   $ source .env/bin/activate
   (.env) $ pip install esbonio

Otherwise the language server will fail to properly understand your project.

If you want to try the latest developments before they are released you can use ``pip`` to install from the development branch.

.. code-block:: console

   $ pip install "git+https://github.com/swyddfa/esbonio#egg=esbonio&subdirectory=lib/esbonio"

For more information on this command see the documentation on pip's `VCS Support <https://pip.pypa.io/en/stable/topics/vcs-support/>`_.


.. relevant-to:: Editor

   VSCode (Esbonio)
      Integration with `VSCode`_ is provided by the `Esbonio`_ extension.

   Emacs (eglot)
      .. include:: ./editors/emacs-eglot/_installation.rst

   Emacs (lsp-mode)
      .. include:: ./editors/emacs-lsp-mode/_installation.rst

   Kate
      .. include:: ./editors/kate/_installation.rst

   Neovim (lspconfig)
      .. include:: ./editors/nvim-lspconfig/_installation.rst

   Vim (coc.nvim)
      .. include:: ./editors/vim-coc/_installation.rst

   Vim (vim-lsp)
      .. include:: ./editors/vim-lsp/_installation.rst

Configuration
-------------

.. relevant-to:: Editor

   VSCode (Esbonio)
      .. include:: ./editors/vscode/_configuration.rst

   Neovim (lspconfig)
      .. include:: ./editors/nvim-lspconfig/_configuration.rst

   Vim (coc.nvim)
      .. include:: ./editors/vim-coc/_configuration.rst

   Vim (vim-lsp)
      .. include:: ./editors/vim-lsp/_configuration.rst

   Emacs (eglot)
      .. include:: ./editors/emacs-eglot/_configuration.rst

   Emacs (lsp-mode)
      .. include:: ./editors/emacs-lsp-mode/_configuration.rst

Sphinx Options
^^^^^^^^^^^^^^

The following options control the creation of the Sphinx application object managed by the server.

.. confval:: sphinx.buildDir (string)

   By default the language server will choose a cache directory (as determined by `appdirs <https://pypi.org/project/appdirs>`_) to place Sphinx's build output.
   This option can be used to force the language server to use a location of your choosing, currently accepted values include:

   - ``/path/to/src/`` - An absolute path
   - ``${workspaceRoot}/docs/src`` - A path relative to the root of your workspace
   - ``${workspaceFolder}/docs/src`` - Same as ``${workspaceRoot}``, placeholder for true multi-root workspace support.
   - ``${confDir}/../src/`` - A path relative to your project's ``confDir``

.. confval:: sphinx.builderName (string)

   By default the language server will use the ``html`` builder.
   This option allows you to specify the builder you wish to use.

   .. note::

      Some features (such as previews) are currently only available for the ``html`` builder.

.. confval:: sphinx.confDir (string)

   The language server attempts to automatically find the folder which contains your project's ``conf.py``.
   If necessary this can be used to override the default discovery mechanism and force the server to use a folder of your choosing.
   Currently accepted values include:

   - ``/path/to/docs`` - An absolute path
   - ``${workspaceRoot}/docs`` - A path relative to the root of your workspace.
   - ``${workspaceFolder}/docs`` - Same as ``${workspaceRoot}``, placeholder for true multi-root workspace support.

.. confval:: sphinx.configOverrides (object)

   This option can be used to override values set in the project's ``conf.py`` file.
   This covers both the :option:`sphinx-build -D <sphinx:sphinx-build.-D>` and :option:`sphinx-build -A <sphinx:sphinx-build.-A>` cli options.

   For example the cli argument ``-Dlanguage=cy`` overrides a project's language, the equivalent setting using the ``configOverrides`` setting would be::

      {
         "sphinx.configOverrides": {
            "language": "cy"
         }
      }

   Simiarly the argument ``-Adocstitle=ProjectName`` overrides the value of the ``docstitle`` variable inside HTML templates, the equivalent setting using ``configOverrides`` would be::

      {
         "sphinx.configOverrides": {
            "html_context.docstitle": "ProjectName"
         }
      }

.. confval:: sphinx.doctreeDir (string)

   This option can be used to specify the directory into which the language server will write the project's doctree cache.
   Currently accepted values include:

   - ``/path/to/docs`` - An absolute path
   - ``${workspaceRoot}/doctrees`` - A path relative to the root of your workspace.
   - ``${workspaceFolder}/doctrees`` - Same as ``${workspaceRoot}``, placeholder for true multi-root workspace support.
   - ``${confDir}/../doctrees`` - A path relative to your project's ``confDir``
   - ``${buildDir}/.doctrees`` - A path relative to your project's ``buildDir``

.. confval:: sphinx.forceFullBuild (boolean)

   Flag that indicates if the server should force a full build of the documentation on startup.
   (Default: ``false``)

.. confval:: sphinx.keepGoing (boolean)

   Continue building even when errors (from warnings) are encountered.
   (Default: ``false``)

.. confval:: sphinx.makeMode (boolean)

   If ``true`` the language server will behave like ``sphinx-build`` when invoked with the :option:`-M <sphinx:sphinx-build.-M>` argument.
   If ``false`` the language server will behave like ``sphinx-build`` when invoked with the :option:`-b <sphinx:sphinx-build.-b>` argument.
   (Default: ``true``)

.. confval:: sphinx.numJobs (string or integer)

   Controls the number of parallel jobs used during a Sphinx build.

   The default value of ``"auto"`` will behave the same as passing ``-j auto`` to a ``sphinx-build`` command.
   Setting this value to ``1`` effectively disables parallel builds.

.. confval:: sphinx.quiet (boolean)

   Hides all standard Sphinx output messages.
   Equivalent to the :option:`sphinx-build -q <sphinx:sphinx-build.-q>` cli option.
   (Default ``false``)

.. confval:: sphinx.silent (boolean)

   Hides all Sphinx output.
   Equivalent to the :option:`sphinx-build -Q <sphinx:sphinx-build.-Q>` cli option.
   (Default ``false``)

.. confval:: sphinx.srcDir (string)

   The language server assumes that your project's ``srcDir`` (the folder containing your rst files) is the same as your projects's ``confDir``.
   If this assumption is not true, you can use this setting to tell the server where to look.
   Currently accepted values include:

   - ``/path/to/src/`` - An absolute path
   - ``${workspaceRoot}/docs/src`` - A path relative to the root of your workspace
   - ``${workspaceFolder}/docs/src`` - Same as ``${workspaceRoot}``, placeholder for true multi-root workspace support.
   - ``${confDir}/../src/`` - A path relative to your project's ``confDir``

.. confval:: sphinx.tags (string[])

   A list of tags to enable.
   See the documentation on the :option:`sphinx-build -t <sphinx:sphinx-build.-t>` cli option for more details.
   (Default: ``[]``)

.. confval:: sphinx.verbosity (integer)

   Set the verbosity level of Sphinx's output. (Default: ``0``)

.. confval:: sphinx.warningIsError (boolean)

   Treat warnings as errors. (Default: ``false``)

Server Options
^^^^^^^^^^^^^^

The following options control the behavior of the language server as a whole.

.. confval:: server.enableScrollSync (boolean)

   When enabled, the server will inject line numbers into HTML build output making it possible for clients to implement synced scrolling.

.. confval:: server.enableLivePreview (boolean)

   When enabled, the server will report diagnostics and build projects taking into account the state of unsaved files.
   **Note:** The server currently relies on the client to tell it when to build unsaved files by issuing a :command:`esbonio.server.build` command.

.. confval:: server.logLevel (string)

   This can be used to set the level of log messages emitted by the server.
   This can be set to one of the following values.

   - ``error`` (default)
   - ``info``
   - ``debug``

.. confval:: server.logFilter (string[])

   The language server will typically include log output from all of its components.
   This option can be used to restrict the log output to be only those named.

.. confval:: server.hideSphinxOutput (boolean)

   .. deprecated:: 0.12.0

      The :confval:`sphinx.quiet (boolean)` and :confval:`sphinx.silent (boolean)` options should be used instead.
      This will be removed in ``v1.0``.

   Normally any build output from Sphinx will be forwarded to the client as log messages.
   If you prefer this flag can be used to exclude any Sphinx output from the log.

.. confval:: server.showDeprecationWarnings (boolean)

   Developer flag which, when enabled, the server will publish any deprecation warnings as diagnostics.


Examples
--------

For some editors where the setup is more manual, we do provide some example configurations
to help get you started.

.. relevant-to:: Editor

   Neovim (lspconfig)
      .. include:: ./editors/nvim-lspconfig/_examples.rst

   Vim (coc.nvim)
      .. include:: ./editors/vim-coc/_examples.rst

   Vim (vim-lsp)
      .. include:: ./editors/vim-lsp/_examples.rst

   Emacs (eglot)
      .. include:: ./editors/emacs-eglot/_examples.rst

   Emacs (lsp-mode)
      .. include:: ./editors/emacs-lsp-mode/_examples.rst

Debugging
---------

In the event that something does not work as expected, you can increase the logging level of the server by setting the :confval:`server.logLevel (string)` option to ``debug``.

.. relevant-to:: Editor

   Neovim (lspconfig)
      .. include:: ./editors/nvim-lspconfig/_debugging.rst

   Vim (coc.nvim)
      .. include:: ./editors/vim-coc/_debugging.rst

   Vim (vim-lsp)
      .. include:: ./editors/vim-lsp/_debugging.rst

Commands
--------

.. relevant-to:: Editor

   VSCode (Esbonio)
      .. include:: editors/vscode/_commands.rst


.. _Esbonio: https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio
.. _open an issue: https://github.com/swyddfa/esbonio/issues/new
.. _VSCode: https://code.visualstudio.com/
