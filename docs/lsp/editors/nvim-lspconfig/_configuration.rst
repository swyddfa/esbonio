The language server's configuration options are passed as ``init_options`` during the server's setup e.g.

.. code-block:: lua

  lspconfig.esbonio.setup {
    init_options = {
      server = {
        logLevel = "debug"
      },
      sphinx = {
        confDir = "/path/to/docs",
        srcDir = "${confDir}/../docs-src"
      }
  }

Here are all the options supported by the server.
