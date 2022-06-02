Within VSCode there is the additional option of enabling logging of all LSP protocol messages by setting the :confval:`esbonio.trace.server (string)` option to ``messages`` or ``verbose``.
This won't give you any more insight into the internal workings of the language server, but can be useful if you want to see exactly what data the server is responding with.

.. code-block:: none

   [Trace - 16:11:00] Sending request 'textDocument/hover - (8)'.
   Params: {
     "textDocument": {
       "uri": "file:///var/home/alex/Projects/esbonio/docs/lsp/editors/vim-lsp/_debugging.rst"
     },
     "position": {
       "line": 0,
       "character": 25
     }
   }

   [Trace - 16:11:00] Received response 'textDocument/hover - (8)' in 4ms.
   Result: {
     "contents": {
       "kind": "markdown",
       "value": "..."
     }
   }

**Note:** This will generate a *lot* of output.
