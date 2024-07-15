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

The following is a list of the availble options.
