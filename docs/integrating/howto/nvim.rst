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
     cmd = {'esbonio', 'server'},
     filetypes = { 'rst' }, -- or 'markdown' if you use MyST
     root_markers = { '.git', 'conf.py' },
   })
   vim.lsp.enable('esbonio')

However, to be useful you will also need to ensure that the :esbonio:conf:`esbonio.sphinx.pythonCommand` and :esbonio:conf:`esbonio.sphinx.buildCommand` options are configured for your project.
The recommended way to do this is via your project's ``pyproject.toml`` file, for example

.. literalinclude:: /pyproject.toml
   :language: toml
   :start-at: [tool.esbonio.sphinx]
   :end-at: pythonCommand

.. tip::

   See :ref:`lsp-configure-sphinx-build-env` and :ref:`lsp-configure-sphinx-build-cmd` guides for more examples of these settings.

If you don't have a ``pyproject.toml`` file, or would prefer to set these options directly in neovim you can include a ``settings`` table


.. code-block:: lua

   vim.lsp.config('esbonio', {
     cmd = {'esbonio'},
     filetypes = { 'rst' }, -- or 'markdown' if you use MyST
     root_markers = { '.git', 'conf.py' },
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
If you want to try it out, you can download it :download:`here <./nvim/init.lua>` and load it by running the command ``nvim -u init.lua``.

.. literalinclude:: ./nvim/init.lua
   :language: lua

.. _integrate-nvim-tips:

Tips and Tricks
---------------

This section contains examples on how you might build on the minimal examples included above

Log to a File
^^^^^^^^^^^^^

By default, ``esbonio`` will log to stderr which can be viewed in neovim's ``lsp.log`` file.
However, it's not necessarily the easiest file to read so you might prefer configuring ``esbonio`` to log to a file instead.

.. code-block:: lua

   vim.lsp.config('esbonio', {
     ...,
     settings = {
       esbonio = {
         logging = {
           level = 'debug',
           filename = 'esbonio.log',
           stderr = false,
         }
       },
     },
   })
   vim.lsp.enable('esbonio')

Provide a Default Build Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have ever used the Esbonio VSCode extension, you may have noticed that it provides a fallback build environment for use with projects that do not provide their own esbonio config.

To replicate the same functionality with neovim, you can provide the :esbonio:conf:`esbonio.sphinx.pythonCommand` setting under the ``init_options`` key.

.. code-block:: lua

   vim.lsp.config('esbonio', {
     ...,
     init_options = {
       esbonio = {
         sphinx = {
           pythonCommand = {'/path/to/fallback/venv/bin/python'},
         }
       },
     },
   })
   vim.lsp.enable('esbonio')

This value will be overidden by any project-local instances of this option.

Sphinx Build Progress Notifications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``esbonio`` uses the :lsp:`window/workDoneProgress/create` mechanism to report the progress of background Sphinx builds.
You can use a plugin like `fidget <https://github.com/j-hui/fidget.nvim>`__ to provide a UI for these.

.. _integrate-nvim-troubleshoot:

Troubleshooting
---------------

The ``:checkhealth vim.lsp`` command will show you details about your current configuration

.. dropdown:: :checkhealth vim.lsp

   .. code-block::

      vim.lsp:                                     require("vim.lsp.health").check()

      - LSP log level : WARN
      - Log path: /var/home/username/.local/state/nvim/lsp.log
      - Log size: 245 KB

      vim.lsp: Active Features ~
      - semantic_tokens
        - Active buffers:

      - document_color
        - Active buffers:

      - folding_range
        - Active buffers:

      - inline_completion
        - Active buffers:


      vim.lsp: Active Clients ~
      - esbonio (id: 1)
        - Version: 2.0.0
        - Root directory: ~/Projects/my-project/docs
        - Command: { "esbonio", "server" }
        - Settings: {
            esbonio = {
              logging = {
                filepath = "esbonio.log",
                level = "debug",
                stderr = false
              }
            }
          }
        - Attached buffers: 1

      vim.lsp: Enabled Configurations ~
      - esbonio:
        - cmd: { "esbonio", "server" }
        - filetypes: rst
        - root_markers: { ".git", "conf.py" }
        - settings: {
            esbonio = {
              logging = {
                filepath = "esbonio.log",
                level = "debug",
                stderr = false
              }
            }
          }


      vim.lsp: File Watcher ~
      - file watching "(workspace/didChangeWatchedFiles)" disabled on all clients

      vim.lsp: Position Encodings ~
      - No buffers contain mixed position encodings
