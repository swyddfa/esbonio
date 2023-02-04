The language server's configuration options are passed as
``initializationOptions`` during the server's setup e.g.

.. code:: json

   {
       "clients": {
           "esbonio": {
               "enabled": true,
               "command": ["esbonio"],
               "selector": "text.restructuredtext",
               "initializationOptions": {
                   "server": {
                       "logLevel": "debug"
                   },
                   "sphinx": {
                     "confDir": "/path/to/docs"
                     "srcDir": "${confDir}/../docs-src"
                   }
               }
           }
       }
   }

Here are all the options supported by the server.
