``esbonio.server.configuration``
   Returns the server's current configuration.

   .. code-block:: json

      {
        "config": {
          "sphinx": {
            "buildDir": "/home/.../docs/_build/html",
            "builderName": "html",
            "confDir": "/home/.../docs",
            "configOverrides": {},
            "doctreeDir": "/home/.../docs/_build/doctrees",
            "forceFullBuild": false,
            "keepGoing": false,
            "makeMode": true,
            "numJobs": 1,
            "quiet": false,
            "silent": false,
            "srcDir": "/home/.../docs",
            "tags": [],
            "verbosity": 0,
            "warningIsError": false,
            "command": [
               "sphinx-build", "-M", "html", "./docs", "./docs/_build",
            ],
            "version": "4.4.0"
          },
          "server": {
            "logLevel": "debug",
            "logFilter": [],
            "hideSphinxOutput": false
          }
        },
        "error": false,
        "warnings": 1
      }

``esbonio.server.preview`` ``{ "show": true }``
   Start a local preview webserver.

   The server will spin up a local :mod:`python:http.server` on a random port in the
   project's configured :confval:`buildDir <sphinx.buildDir (string)>` which can be used to
   preview the result of building the project. The server will return an object like the
   following.

   .. code-block:: json

      { "port": 12345 }

   This command also accepts a parameters object with the following structure

   .. code-block:: json

      { "show": true }

   By default the ``show`` parameter will default to ``true`` which means the server will
   also send a :lsp:`window/showDocument` request, asking the client to open the preview in a
   web browser.

   If a client wants to implement its own preview mechanism (like the `VSCode Extension <https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio>`_)
   it can set ``show`` to ``false`` to suppress this behavior.
