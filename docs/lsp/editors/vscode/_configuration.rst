
Configuration is handled using VSCode's settings system.
The following options are available.

.. confval:: esbonio.server.enabled (boolean)

   A flag that can be used to completely disable the language server, if required.

.. confval:: esbonio.server.pythonPath (string)

   If the official `Python Extension`_ is available the extension will use the same
   Python environment as you have configured for your workspace. However, if you wish
   to use a different environment or do not have the Python extension installed this
   option can be set to tell the extension which environment to use.

   Currently accepted values include:

   - ``/path/to/python/`` - An absolute path
   - ``${workspaceRoot}/../venv/bin/python`` - A path relative to the root of your workspace

.. confval:: esbonio.server.installBehavior (string)

   The VSCode extension can manage the installation of the language server for you.
   If the language server is missing from your current environment the extension will prompt
   by default to check if you want it to perform the installation. If you don't like this
   behavior you can use this option to change it, the following values are valid

   - ``nothing`` - Don't attempt to install the language server if it's missing
   - ``prompt`` (default) - Ask for confirmation before installing the server
   - ``automatic`` - Never ask for confirmation, the language server will be installed
     automatically in new environments

.. confval:: esbonio.server.updateFrequency (string)

   The VSCode extension can also automatically install updates to the language server
   as they are released. By default the extension will check on start up once a week,
   alternatively you can set this setting to one of the following values

   - ``never`` - Never check for updates. Though you can still trigger an update
     manually if you wish.
   - ``monthly`` - Check for updates once a month
   - ``weekly`` - Check for updates once a week
   - ``daily`` - Check for updates once a day

.. confval:: esbonio.server.updateBehavior (string)

   If an update is detected through one of the extension's automated checks this option
   controls what the extension does next. By default the extension will automatically
   install it **unless** it is a major update (e.g ``1.x.y`` -> ``2.0.0``). The following
   options are available

   - ``promptAlways`` - Always ask for confirmation before applying updates
   - ``promptMajor`` - Only ask for confirmation on major updates, minor versions will be
     installed automatically
   - ``automatic`` - Never ask for confirmation, updates will always be installed.

.. confval:: esbonio.trace.server (string)

   Set the logging level for LSP protocol messages, mostly useful for debugging.

   The following options are available

   - ``off`` (default) - Don't log any LSP messages
   - ``messages`` - Log when LSP messages are sent/recevied
   - ``verbose`` - Log all LSP messages and their contents

The VSCode extension also exposes the following server configuration options under an
``esbonio.*`` prefix.

.. _Python Extension: https://marketplace.visualstudio.com/items?itemName=ms-python.python
