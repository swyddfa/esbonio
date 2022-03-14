
``esbonio/buildStart``
   Emitted whenever a Sphinx build is started.

   .. code-block:: json

      {}

``esbonio/buildComplete``
  Emitted whenever a Sphinx build is complete.

  .. code-block:: json

     {
       "config": {
         "sphinx": {
            "version": "4.4.0",
            "confDir": "/home/.../docs",
            "srcDir": "/home/.../docs",
            "buildDir": "/home/.../docs/_build/html",
            "builderName": "html"
         },
         "server": {
            "log_level": "debug",
            "log_filter": [],
            "hide_sphinx_output": false
         }
       },
       "error": false,
       "warnings": 0
     }
