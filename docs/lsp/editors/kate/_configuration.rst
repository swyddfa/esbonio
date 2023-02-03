The settings that go in the :guilabel:`User Server Settings` tab of the LSP Client configuration section will apply globally to all your projects.
Settings that you want to only apply to a specific project can go in your project's ``.kateproject`` file.

As an example, the following ``.kateproject`` file sets a custom start command to use a specific Python environment along with specifying the sphinx build dir.

.. code-block:: json

   {
     "name": "Esbonio",
     "files": [
       {
         "git": 1
       }
     ],
     "lspclient": {
       "servers": {
         "rst": {
           "command": ["/path/to/venv/bin/python", "-m", "esbonio"],
           "initializationOptions": {
             "sphinx": {
               "buildDir": "${confDir}/_build"
             },
             "server": {
               "logLevel": "debug"
             }
           }
         }
       }
     }
   }

The values in the ``lspclient`` section will be merged with the values specified in :guilabel:`User Server Settings`.

See below for a list of all available configuration options.
