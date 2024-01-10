How To use Esbonio in Neovim
============================

This guide covers how to setup ``esbonio`` with Neovim's built-in language client.

.. highlight:: none

Installation
------------

Install the language server using `pipx <https://pipx.pypa.io/stable/>`__::

   pipx install esbonio

Configuration
-------------

The
`nvim-lspconfig <https://github.com/neovim/nvim-lspconfig>`_
plugin provides a
`base configuration <https://github.com/neovim/nvim-lspconfig/blob/master/lua/lspconfig/server_configurations/esbonio.lua>`__
for the language server.

It's recommeded that any configuration settings specific to your project (such as your ``sphinx-build`` command) are stored in your project's ``pyproject.toml`` file.
Settings specific to you (such as your Python environment) are provided via the ``settings`` table passed to ``lspconfig.esbonio.setup {}``.

.. code-block:: lua

   lspconfig.esbonio.setup {
     settings = {
       sphinx = {
         pythonCommand = { "/path/to/project/.venv/bin/python" },
       }
     }
   }

.. important::

   You must provide a value for :esbonio:conf:`esbonio.sphinx.pythonCommand` so that ``esbonio`` can build your documentation correctly.

See :ref:`lsp-configuration` for a complete reference of all configuration options supported by the server.

.. _lsp-nvim-python-discovery:

Python Discovery
^^^^^^^^^^^^^^^^

The most important setting to get right is to give ``esbonio`` the correct Python environment to use when building your documentation.

The simplest option is to hardcode the right environment into your configuration as the example above shows.
However, if you change between projects often, constantly updating this value in your configuration is going to get tedious very quickly.

Another option is to include a function in your configuration that will automatically choose the correct one for you.
For example the ``find_venv`` function below implements the following discovery rules.

- If ``nvim`` is launched with a virtual environment active, use it, otherwise
- Look for a virtual environment located within the project's git repository

.. literalinclude:: ../editors/nvim-lspconfig/init.vim
   :language: lua
   :start-at: function find_venv()
   :end-before: lspconfig

Be sure to pass the result of such a function to the server

.. code-block:: lua

   lspconfig.esbonio.setup {
     settings = {
       sphinx = { pythonCommand = find_venv() }
     }
   }

Example
-------

.. admonition:: Do you use Nix?

   If you have the `Nix <https://nixos.org/>`__ package manager on your machine you can try out our example configuration with the following command::

      nix run github:swyddfa/esbonio#nvim

There is an opionated, ready out of the box example configuration you can try, or at least get inspiration from.
This configuration includes:

- Automatic python environment discovery (using the example logic in `lsp-nvim-python-discovery`_)
- Live preview and synchronized scrolling
- A VSCode style log output window (using `toggleterm`_ and `lsp-devtools`_)
- Notifications and progress updates via `fidget`_
- "Standard" neovim plugins including `telescope`_

.. _fidget: https://github.com/j-hui/fidget.nvim
.. _lsp-devtools: https://github.com/swyddfa/esbonio
.. _telescope: https://github.com/nvim-telescope/telescope.nvim
.. _toggleterm: https://github.com/akinsho/toggleterm.nvim

.. dropdown:: Show Example Config

   You can also :download:`download <../editors/nvim-lspconfig/init.vim>` this file

   .. literalinclude:: ../editors/nvim-lspconfig/init.vim
      :language: vim


Troubleshooting
---------------

You will also have to increase the LSP logging level in Neovim itself.

.. code-block:: vim

   lua << EOF
   vim.lsp.set_log_level("debug")
   EOF

You can then open the log file with the command ``:LspLog``.
See `here <https://github.com/neovim/nvim-lspconfig/#troubleshooting>`_ for more details.
