You will also have to increase the LSP logging level in Vim itself.

.. code-block:: vim

   let g:lsp_log_verbose = 1
   let g:lsp_log_file = expand('~/vim-lsp.log')
