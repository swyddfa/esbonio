Vim/Neovim - vim-lsp
====================

.. figure:: /images/nvim-vim-lsp.png
   :align: center
   :width: 80%

   Using Esbonio and Neovim with ``vim-lsp``

.. include:: _vim-intro.rst

.. highlight:: none

This page documents how you can use the Esbonio language server with `vim-lsp`_


Setup
-----

Basic configuration for the language server is provided by the
`vim-lsp-settings <https://github.com/mattn/vim-lsp-settings>`_ plugin.

.. tabbed:: vim-plug

   .. literalinclude:: nvim/vim-lsp.vim
      :language: vim
      :start-at: set expandtab

   To try this configuration on your machine.

   1. Make sure that you've followed the :ref:`editor_integration_setup`.
   2. Download :download:`vim-lsp.vim <nvim/vim-lsp.vim>` to a folder of your choosing.
   3. Ensure that you have vim-plug's ``plug.vim`` file installed in your autoload directory.
      See `this guide <https://github.com/junegunn/vim-plug#installation>`_ for details.
   4. Open a terminal in the directory containing this file and run the following command
      to load this config isolated from your existing configuration::

         (n)vim -u vim-lsp.vim
   5. Install the required plugins::

         :PlugInstall

As mentioned in the :ref:`common setup <editor_integration_setup>`, the language server works
best when it's run from the same Python environment as the one used to build your documentation.
The easiest way to make sure ``(n)vim`` uses the right Python interpreter, is to activate your
environment before launching ``(n)vim``::

          $ source .env/bin/activate
   (.env) $ (n)vim

Configuration
-------------

The language server's configuration options can be passed a ``initialization_options`` during the
server's setup. These can be set on a per-project basis by creating a ``.vim-lsp-settings/settings.json``
file in the root of your project

.. code-block:: json

   {
     "esbonio": {
       "initialization_options": {
         "server": {
           "logLevel": "debug"
         },
         "sphinx": {
           "confDir": "/path/to/docs",
           "srcDir": "${confDir}/../docs-src"
         }
       }
     }
   }

See :ref:`here <editor_integration_config>` for a full list of supported options.

Debugging
---------

In the event of something not working as you'd expect you can set the following options to enable logging.
See `here </home/alex/Projects/esbonio/docs/images/nvim-vim-lsp.png>`_ for more details.

.. code-block:: vim

   let g:lsp_log_verbose = 1
   let g:lsp_log_file = expand('~/vim-lsp.log')

Be sure to also increase the log level of Esbonio by setting the ``server.logLevel`` initialization option
to ``debug``
