.. highlight:: none

Basic configuration for the language server is provided through the
`nvim-lspconfig <https://github.com/neovim/nvim-lspconfig>`_ plugin

.. literalinclude:: ./editors/nvim-lspconfig/init.vim
   :language: vim
   :start-at: set expandtab

As mentioned above the language server works best
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
