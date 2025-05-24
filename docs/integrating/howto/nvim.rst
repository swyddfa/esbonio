.. _integrate-nvim:

How To Integrate Esbonio with Neovim
====================================

This guide covers how to setup ``esbonio`` with Neovim's built-in language client.

.. highlight:: none

Installation
------------

.. include:: /_includes/installation.rst

.. _integrate-nvim-config:

Configuration
-------------

Every Neovim configuration is unique, so we provide just a minimal example configuration that uses the ``vim.lsp.config()`` mechanism introduced in Neovim v0.11.
See the :ref:`integrate-nvim-tips` section below for examples on how you might want to extend your configuration once you have the basics setup.

The following configuration should be all you need to instruct Neovim to launch the ``esbonio`` language server within your Sphinx projects.

.. code-block:: lua

   vim.lsp.config('esbonio', {
     cmd = {'esbonio'},
     filetypes = { 'rst' }, -- or 'markdown' if you use MyST
     root_markers = { '.git' },
   })
   vim.lsp.enable('esbonio')

However, to be useful you will also need to ensure that the :esbonio:conf:`esbonio.sphinx.pythonCommand` and :esbonio:conf:`esbonio.sphinx.buildCommand` options are configured for your project.
The recommended way to do this is via your project's ``pyproject.toml`` file, for example

.. literalinclude:: /pyproject.toml
   :language: toml
   :start-at: [tool.esbonio.sphinx]
   :end-at: pythonCommand

.. tip::

   See :ref:`lsp-use-with` and :ref:`lsp-configure-python` guides for more examples of these settings.

If you don't have a ``pyproject.toml`` file, or would prefer to set these options directly in neovim you can include a ``settings`` table


.. code-block:: lua

   vim.lsp.config('esbonio', {
     cmd = {'esbonio'},
     filetypes = { 'rst' }, -- or 'markdown' if you use MyST
     root_markers = { '.git' },
     settings = {
       esbonio = {
         sphinx = {
           buildCommand = {'sphinx-build', '-M', 'dirhtml', '.', '${defaultBuildDir}'},
           pythonCommand = {'hatch', '-e', 'docs', 'run', 'python'},
         }
       },
     },
   })
   vim.lsp.enable('esbonio')

The ``settings`` table can be used to set any configuration value supported by the server.
See the :ref:`Configuration Reference <lsp-configuration>` for details on all available options.

.. _integrate-nvim-example:

Example
-------

See the ``init.lua`` file below for a complete, minimal example configuration.
You can download it :download:`here <./nvim/init.lua>` and load it by running ``nvim -u init.lua``.

.. literalinclude:: ./nvim/init.lua
   :language: lua

.. _integrate-nvim-tips:

Tips and Tricks
---------------

**sphinx-build progress notifications**

``esbonio`` uses the :lsp:`window/workDoneProgress/create` mechanism to report the progress of background Sphinx builds.
You can use a plugin like `fidget <https://github.com/j-hui/fidget.nvim>`__ to provide a UI for these.

.. _integrate-nvim-troubleshoot:

Troubleshooting
---------------

The ``:checkhealth vim.lsp`` command will show you details about your current configuration

.. dropdown:: :checkhealth vim.lsp

   .. code-block::

      vim.lsp:                                     require("vim.lsp.health").check()

      - LSP log level : DEBUG
      - ⚠️ WARNING Log level DEBUG will cause degraded performance and high disk usage
      - Log path: /var/home/username/.local/state/nvim/lsp.log
      - Log size: 267 KB

      vim.lsp: Active Clients ~
      - esbonio (id: 1)
        - Version: 1.0.0b11
        - Root directory: /tmp/rst
        - Command: { "esbonio" }
        - Settings: {
            esbonio = {
              logging = {
                level = "debug"
              },
              sphinx = {
                buildCommand = { "sphinx-build", ".", "./_build" },
                pythonCommand = { "python" }
              }
            }
          }
        - Attached buffers: 1

      vim.lsp: Enabled Configurations ~
      - esbonio:
        - cmd: { "esbonio" }
        - filetypes: rst
        - root_markers: .git
        - settings: {
            esbonio = {
              logging = {
                level = "debug"
              },
              sphinx = {
                buildCommand = { "sphinx-build", ".", "./_build" },
                pythonCommand = { "python" }
              }
            }
          }


      vim.lsp: File Watcher ~
      - file watching "(workspace/didChangeWatchedFiles)" disabled on all clients

      vim.lsp: Position Encodings ~
      - No buffers contain mixed position encodings
