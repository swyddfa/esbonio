You will also have to increase the LSP logging level in Neovim itself.

.. code-block:: vim

   lua << EOF
   vim.lsp.set_log_level("debug")
   EOF

You can then open the log file with the command ``:lua vim.cmd('e'..vim.lsp.get_log_path())``.
See `here <https://github.com/neovim/nvim-lspconfig/#debugging>`_ for more details.
