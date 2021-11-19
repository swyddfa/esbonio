Vim/Neovim - coc.nvim
=====================

.. figure:: /images/nvim-coc.png
   :align: center
   :width: 80%

   Using Esbonio and Neovim with ``coc.nvim``.

.. include:: _vim-intro.rst

.. highlight:: none

This page documents how you can use the Esbonio langauge server with `coc.nvim`_ thanks
to the `coc-esbonio <https://github.com/yaegassy/coc-esbonio>`_ extension.

Setup
-----

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
-------------

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

Debugging
---------

In the event of something not working as you'd expect you can use the command
``:CocCommand workspace.showOutput`` to view log output from Esbonio. Be sure to set the ``server.logLevel``
initialization option to ``debug``.

See coc.nvim's `readme <https://github.com/neoclide/coc.nvim#trouble-shooting>`_ and
`wiki <https://github.com/neoclide/coc.nvim/wiki/Debug-language-server>`_ for more details.
