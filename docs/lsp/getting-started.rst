.. _lsp_getting_started:

Getting Started
===============

This section contains notes on how to use the Language Server with your text
editor of choice.


.. relevant-to:: VSCode
   :category: Editor

   .. figure:: /images/vscode-screenshot.png
      :align: center
      :target: /_images/vscode-screenshot.png

      The VSCode extension in action.

.. relevant-to:: Emacs (eglot)
   :category: Editor

   .. figure:: /images/emacs-eglot-extended.png
      :align: center
      :target: /_images/emacs-eglot-extended.png

      Emacs, Esbonio and the ``eglot-extended.el`` configuration

.. relevant-to:: Emacs (lsp-mode)
   :category: Editor

   .. figure:: /images/emacs-lsp-mode-extended.png
      :align: center
      :target: /_images/emacs-lsp-mode-extended.png

      Emacs, Esbonio and the ``lsp-mode-extended.el`` configuration

.. relevant-to:: Kate
   :category: Editor

   .. figure:: /images/kate-screenshot.png
      :align: center
      :target: /_images/kate-screenshot.png

      Using the Esbonio language server within Kate.

   `Kate <https://kate-editor.org/en-gb/>`_ is a text editor from the KDE project
   and comes with LSP support.

.. relevant-to:: Neovim (lspconfig)
   :category: Editor

   .. figure:: /images/nvim-lspconfig.png
      :align: center
      :target: /_images/nvim-lspconfig.png

      Using Esbonio with Neovim's built-in language client.

.. relevant-to:: Vim (coc.nvim)
   :category: Editor

   .. figure:: /images/nvim-coc.png
      :align: center
      :target: /_images/nvim-coc.png

      Using Esbonio in Neovim via ``coc.nvim`` and the ``coc-esbonio`` extension.

.. relevant-to:: Vim (vim-lsp)
   :category: Editor

   .. figure:: /images/nvim-vim-lsp.png
      :align: center
      :target: /_images/nvim-vim-lsp.png

      Using Esbonio and Neovim with ``vim-lsp``

.. admonition:: Don't see your favourite editor?

   Feel free to submit a pull request with steps on how to get started or if you're not
   sure on where to start, `open an issue`_ and we'll help you figure it out.


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


.. relevant-to:: VSCode
   :category: Editor

   Integration with `VSCode`_ is provided by the `Esbonio`_ extension.

.. relevant-to:: Emacs (eglot)
   :category: Editor

   .. include:: ./editors/emacs-eglot/_installation.rst

.. relevant-to:: Emacs (lsp-mode)
   :category: Editor

   .. include:: ./editors/emacs-lsp-mode/_installation.rst

.. relevant-to:: Kate
   :category: Editor

   .. include:: ./editors/kate/_installation.rst

.. relevant-to:: Neovim (lspconfig)
   :category: Editor

   .. include:: ./editors/nvim-lspconfig/_installation.rst

.. relevant-to:: Vim (coc.nvim)
   :category: Editor

   .. include:: ./editors/vim-coc/_installation.rst

.. relevant-to:: Vim (vim-lsp)
   :category: Editor

   .. include:: ./editors/vim-lsp/_installation.rst

Configuration
-------------

.. relevant-to:: VSCode
   :category: Editor

   .. include:: ./editors/vscode/_configuration.rst

.. relevant-to:: Neovim (lspconfig)
   :category: Editor

   .. include:: ./editors/nvim-lspconfig/_configuration.rst

.. relevant-to:: Vim (coc.nvim)
   :category: Editor

   .. include:: ./editors/vim-coc/_configuration.rst

.. relevant-to:: Vim (vim-lsp)
   :category: Editor

   .. include:: ./editors/vim-lsp/_configuration.rst

.. relevant-to:: Emacs (eglot)
   :category: Editor

   .. include:: ./editors/emacs-eglot/_configuration.rst

.. relevant-to:: Emacs (lsp-mode)
   :category: Editor

   .. include:: ./editors/emacs-lsp-mode/_configuration.rst

.. confval:: sphinx.buildDir (string)

   By default the language server will choose a cache directory (as determined by
   `appdirs <https://pypi.org/project/appdirs>`_) to put Sphinx's build output.
   This option can be used to force the language server to use a location
   of your choosing, currently accepted values include:

   - ``/path/to/src/`` - An absolute path
   - ``${workspaceRoot}/docs/src`` - A path relative to the root of your workspace
   - ``${workspaceFolder}/docs/src`` - Same as ``${workspaceRoot}``, placeholder for true multi-root workspace support.
   - ``${confDir}/../src/`` - A path relative to your project's ``confDir``

.. confval:: sphinx.confDir (string)

   The language server attempts to automatically find the folder which contains your
   project's ``conf.py``. If necessary this can be used to override the default discovery
   mechanism and force the server to use a folder of your choosing. Currently accepted
   values include:

   - ``/path/to/docs`` - An absolute path
   - ``${workspaceRoot}/docs`` - A path relative to the root of your workspace.
   - ``${workspaceFolder}/docs`` - Same as ``${workspaceRoot}``, placeholder for true multi-root workspace support.

.. confval:: sphinx.srcDir (string)

   The language server assumes that your project's ``srcDir`` (the folder containing your
   rst files) is the same as your projects's ``confDir``. If this assumption is not true,
   you can use this setting to tell the server where to look. Currently accepted values
   include:

   - ``/path/to/src/`` - An absolute path
   - ``${workspaceRoot}/docs/src`` - A path relative to the root of your workspace
   - ``${workspaceFolder}/docs/src`` - Same as ``${workspaceRoot}``, placeholder for true multi-root workspace support.
   - ``${confDir}/../src/`` - A path relative to your project's ``confDir``

.. confval:: sphinx.forceFullBuild (boolean)

   Flag that indicates if the server should force a full build of the documentation on startup. (Default: ``true``)

.. confval:: server.logLevel (string)

   This can be used to set the level of log messages emitted by the server. This can be set
   to one of the following values.

   - ``error`` (default)
   - ``info``
   - ``debug``

.. confval:: server.logFilter (string[])

   The language server will typically include log output from all of its components. This
   option can be used to restrict the log output to be only those named.

.. confval:: server.hideSphinxOutput (boolean)

   Normally any build output from Sphinx will be forwarded to the client as log messages.
   If you prefer this flag can be used to exclude any Sphinx output from the log.

Examples
--------

For some editors where the setup is more manual, we do provide some example configurations
to help get you started.

.. relevant-to:: Neovim (lspconfig)
   :category: Editor

   .. include:: ./editors/nvim-lspconfig/_examples.rst

.. relevant-to:: Vim (coc.nvim)
   :category: Editor

   .. include:: ./editors/vim-coc/_examples.rst

.. relevant-to:: Vim (vim-lsp)
   :category: Editor

   .. include:: ./editors/vim-lsp/_examples.rst

.. relevant-to:: Emacs (eglot)
   :category: Editor

   .. include:: ./editors/emacs-eglot/_examples.rst

.. relevant-to:: Emacs (lsp-mode)
   :category: Editor

   .. include:: ./editors/emacs-lsp-mode/_examples.rst

Debugging
---------

In the event that something does not work as expected, you can increase the
logging level of the server by setting the ``server.logLevel`` initialization option
to ``debug``.

.. relevant-to:: Neovim (lspconfig)
   :category: Editor

   .. include:: ./editors/nvim-lspconfig/_debugging.rst

.. relevant-to:: Vim (coc.nvim)
   :category: Editor

   .. include:: ./editors/vim-coc/_debugging.rst

.. relevant-to:: Vim (vim-lsp)
   :category: Editor

   .. include:: ./editors/vim-lsp/_debugging.rst

Additional Details
------------------

.. relevant-to:: VSCode
   :category: Editor


   Commands
   """"""""

   .. include:: editors/vscode/_commands.rst

   Changelog
   """""""""

   .. include:: ../../code/CHANGES.rst


.. _Esbonio: https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio
.. _open an issue: https://github.com/swyddfa/esbonio/issues/new
.. _VSCode: https://code.visualstudio.com/
