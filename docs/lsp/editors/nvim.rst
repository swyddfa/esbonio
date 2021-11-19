Neovim - lspconfig
==================

.. figure:: /images/nvim-lspconfig.png
   :align: center
   :width: 80%

   Using Esbonio and Neovim with the built in language client.

.. include:: _vim-intro.rst

.. highlight:: none

This page documents how you can use the Esbonio language server with the built in
`neovim`_  language client.

Setup
-----

Basic configuration for the language server is provided through the
`nvim-lspconfig <https://github.com/neovim/nvim-lspconfig>`_ plugin

.. tabbed:: vim-plug

   .. literalinclude:: nvim/nvim-lspconfig.vim
      :language: vim
      :start-at: set expandtab

   To try this configuration on your machine.

   1. Make sure that you've folllowed the :ref:`editor_integration_setup`.
   2. Download :download:`nvim-lspconfig.vim <nvim/nvim-lspconfig.vim>` to a folder
      of your choosing.
   3. Ensure you have vim-plug's ``plug.vim`` file installed in your autoload
      directory. See
      `this guide <https://github.com/junegunn/vim-plug#installation>`_ for
      details.
   4. Open a terminal in the directory containing this file and run the
      following command to load this config isolated from your existing
      configuration::

         nvim -u nvim-lspconfig.vim

   5. Install the ``nvim-lspconfig`` plugin::

         :PlugInstall

As mentioned in the :ref:`common setup <editor_integration_setup>` the language server works best
when it's run from the same Python environment as the one used to build your documentation. The
easiest way to make sure ``nvim`` uses the right Python interpreter, is to activate your environment
before launching ``nvim``::

          $ source .env/bin/activate
   (.env) $ nvim

Alternatively, you can change the default command to launch the language sever with a particular
interpreter

.. code-block:: lua

   lspconfig.esbonio.setup {
     cmd = { '/path/to/virtualenv/bin/python', '-m', 'esbonio' }
   }

Configuration
-------------

The language server's configuration options can be passed as ``init_options`` during the server's setup.

.. code-block:: lua

  lspconfig.esbonio.setup {
    init_options = {
      server = {
        logLevel = "debug"
      },
      sphinx = {
        confDir = "/path/to/docs",
        srcDir = "${confDir}/../docs-src"
      }
  }

See :ref:`here <editor_integration_config>` for a full list of supported options.

Debugging
---------

In the event of something not working as you'd expect you can set the following option to enable logging.
Don't forget to also increase the log level of Esbonio by setting the ``server.logLevel`` initialization option
to ``debug``.

.. code-block:: vim

   lua << EOF
   vim.lsp.set_log_level("debug")
   EOF

You can then open the log file with the command ``:lua vim.cmd('e'..vim.lsp.get_log_path())``.
See `here <https://github.com/neovim/nvim-lspconfig/#debugging>`_ for more details.
