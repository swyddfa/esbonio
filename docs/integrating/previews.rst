Live Previews
=============

.. note::

   Currently live previews are only implemented for builders that produce HTML output.

``esbonio`` is able to offer a preview of your documentation that is automatically updated as you work.

While the preview functionality tries to leverage existing LSP methods where possible, there are some features that require extra methods to enable.
This page provides all the details you will need to enable live previews in your language client of choice.

Basic Previews
--------------

To trigger a preview for a file, your language client will need to invoke the following command using the :lsp:`workspace/executeCommand` request from the Language Server Protocol.

.. esbonio:command:: esboino.server.previewFile

   Generate and open the preview for the given file.

   This command requires the following arguments

   .. code-block:: json

      [
        {"uri": "file:///path/to/file/to/preview.rst"}
      ]

   The server will then look up the output file that corresponds with the given uri, if no such file exists, the server will do nothing and return a ``null`` response.

   Assuming the output file exists and your language client supports it the server will send a :lsp:`window/showDocument` request to open the resulting HTML file in your web browser.

   However, to handle the case where your client does not support :lsp:`window/showDocument` the server will also return the following object allowing you to open the corresponding uri yourself.

   .. code-block:: json

      {"uri": "http://localhost:1234/preview.html?ws=56789"}

Implementing this single command will give you a fairly good preview experience.

- The preview will automatically reload each time a Sphinx build completes.
- Assuming your client supports the ``selection`` field of a ``window/showDocument`` request, scrolling the preview window will automatically scroll your editor window to match.
- To preview another file, send another ``esbonio.server.previewFile`` command. Depending on your language client, you might be able to `automate this <https://github.com/swyddfa/esbonio/blob/12c9bd93b9b43eaa5538a0dc8047e966dcbf68e8/code/src/node/preview.ts#L38>`__

Synchronised Scrolling
----------------------

However, to implement full synchronised scrolling you will need your client to send the following custom notification each time you scroll your editor.

.. esbonio:command:: view/scroll

   Scroll the preview to reveal the given line number.
   This requires the following parameters

   .. code-block:: json

      {"uri": "file:///path/to/file/to/preview.rst", "line": 10}

   Where ``line`` is the line number visible at the very top of your editor window.
   The ``uri`` of the current file is also required since output files can contain the contents of one or more input files (e.g. using the ``.. include::`` directive).

Example Implementation
-----------------------

.. tip::

   For a more complete example, see the preview implementation in the `Esbonio VSCode Extension <https://github.com/swyddfa/esbonio/blob/develop/code/src/node/preview.ts>`__


The following is just enough configuration to enable live previews with synchronised scrolling in Neovim.
There are likely some quality of life improvements you would want to make to this, but it's enough to get something up and running.

This example

- Adds a ``:EsbonioPreviewFile`` command to generate the preview for the current file
- Relies on Neovim's built in :lsp:`window/showDocument` handler both to open the preview in your default web browser and synchronise the preview's scroll state with the editor.
- Sets up an autocmd for the ``WinScrolled`` event to synchronise the editor's scroll state with the preview.

.. code-block:: lua

   require('lspconfig').esbonio.setup {
     commands = {
       EsbonioPreviewFile = {
         preview_file,
         description = 'Preview Current File',
       },
     },
   }

Where the ``preview_file`` function sends the :command:`esbonio.server.previewFile` command and sets up the ``WinScrolled`` autocommand.

.. code-block:: lua

   function preview_file()
     local params = {
       command = 'esbonio.server.previewFile',
       arguments = {
         { uri = vim.uri_from_bufnr(0) },
       },
     }

     local clients = require('lspconfig.util').get_lsp_clients {
       bufnr = vim.api.nvim_get_current_buf(),
       name = 'esbonio',
     }
     for _, client in ipairs(clients) do
       client.request('workspace/executeCommand', params, nil, 0)
     end

     local augroup = vim.api.nvim_create_augroup("EsbonioSyncScroll", { clear = true })
     vim.api.nvim_create_autocmd({"WinScrolled"}, {
       callback = scroll_view, group = augroup, buffer = 0
     })
   end

And the ``scroll_view`` command sends the required ``view/scroll`` notification with the server.

.. code-block:: lua

   function scroll_view(event)
     local esbonio = vim.lsp.get_active_clients({ bufnr = 0, name = 'esbonio' })[1]
     local view = vim.fn.winsaveview()

     local params = { uri = vim.uri_from_bufnr(0),  line = view.topline }
     esbonio.notify('view/scroll', params)
   end
