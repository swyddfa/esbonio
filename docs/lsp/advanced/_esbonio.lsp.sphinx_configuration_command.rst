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
