Neovim (nvim-lspconfig)
=======================

.. figure:: /images/nvim-lspconfig.png
   :align: center

   Using esbonio with Neovim's built in language client

This guide covers how to setup ``esbonio`` with Neovim's built-in language client.

.. highlight:: none

Installation
------------

.. include:: ./_installation.rst


Configuration
-------------

`Basic configuration <https://github.com/neovim/nvim-lspconfig/blob/master/lua/lspconfig/server_configurations/esbonio.lua>`__
for the language server is available through the
`nvim-lspconfig <https://github.com/neovim/nvim-lspconfig>`_
plugin.


Configuration settings are provided via the ``settings`` table passed to ``lspconfig.esbonio.setup {}``.
Perhaps the most important setting is :confval:`esbonio.sphinx.pythonCommand (string[])` which tells the server which Python envrionment to use when building your documentation.

Another important setting is :confval:`esbonio.sphinx.buildCommand (string[])` which tells the server the command you use to build your documentation.

.. code-block:: lua

   lspconfig.esbonio.setup {
     settings = {
       sphinx = {
         pythonCommand = { "/path/to/project/.venv/bin/python" },
         buildCommand = { "sphinx-build", "-M", "html", "docs", "docs/_build" },
       }
   }

See :ref:`lsp-configuration` for a complete reference of all configuration options supported by the server.

Examples
--------

.. admonition:: Do you use Nix?

   If you have the `Nix <https://nixos.org/>`__ package manager on your machine you can try out our example configuration with the following command::

      nix run github:swyddfa/esbonio/beta#nvim-lspconfig

To try the example configuration on your machine.

#. Download :download:`init.vim <nvim-lspconfig/init.vim>` to a folder of your choosing.
#. Ensure you have the `nvim-lspconfig`_ plugin installed.
#. Open a terminal in the directory containing this file and run the following command to load this config isolated from your existing configuration::

      nvim -u init.vim

Troubleshooting
---------------

You will also have to increase the LSP logging level in Neovim itself.

.. code-block:: vim

   lua << EOF
   vim.lsp.set_log_level("debug")
   EOF

You can then open the log file with the command ``:LspLog``.
See `here <https://github.com/neovim/nvim-lspconfig/#troubleshooting>`_ for more details.
