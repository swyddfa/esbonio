Vim/Neovim
==========

There are multiple ways to make use of a language server within the vim ecosystem.

- `coc.nvim`_ a fully featured language client that aims to closely follow the
  way VSCode works. Despite what the name implies it includes supports for both
  vim8 and neovim
- `vim-lsp`_ an async LSP plugin for vim8 and neovim.
- `neovim`_ neovim v0.5+ comes with built-in support for the language server protocol.

.. _coc.nvim: https://github.com/neoclide/coc.nvim
.. _vim-lsp: https://github.com/prabirshrestha/vim-lsp
.. _neovim: https://neovim.io/doc/user/lsp.html


This page contains a number of sample configurations that you can use to get started.

Coc.nvim
---------

.. figure:: /images/nvim-coc.png
   :align: center
   :width: 80%

   Using Esbonio and Neovim with the ``esbonio-coc.vim`` config.

Setup
^^^^^

.. tabbed:: vim-plug

   .. literalinclude:: nvim/esbonio-coc.vim
      :language: vim
      :start-at: set expandtab

   To try this configuration on your machine.

   1. Make sure that you've folllowed the :ref:`editor_integration_setup`.
   2. Download :download:`esbonio-coc.vim <nvim/esbonio-coc.vim>` to a folder
      of your choosing.
   3. Ensure you have vim-plug's ``plug.vim`` file installed in your autoload
      directory. See
      `this guide <https://github.com/junegunn/vim-plug#installation>`_ for
      details.
   4. Open a terminal in the directory containing this file and run the
      following command to load this config isolated from your existing
      configuration::

         (n)vim -u esbonio-coc.vim

   5. Install the coc.nvim plugin::

         :PlugInstall

   6. Install the coc-esbonio extension::

         :CocInstall coc-esbonio

Configuration
^^^^^^^^^^^^^

The language server provides a number of :ref:`configuration <editor_integration_config>`
values these can be set in coc.nvim's ``coc-settings.json`` configuration file, for
example

.. code-block:: json

   {
     "esbonio.sphinx.confDir": "${workspaceRoot}/docs",
     "esbonio.sphinx.srcDir": "${confDir}/../src"
   }

See coc.nvim's `documentation <https://github.com/neoclide/coc.nvim/wiki/Using-the-configuration-file>`_
for more details.
