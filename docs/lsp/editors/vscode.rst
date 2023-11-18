Visual Studio Code
==================

.. figure:: /images/vscode-screenshot.png
   :align: center
   :target: /_images/vscode-screenshot.png

   Integration with VSCode is provided by the `Esbonio`_ extension

Installation
------------

The language server is included with the VSCode extension itself and does not need to be installed separately.

.. _Esbonio: https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio


Configuration
--------------

In addition to the standard :ref:`lsp-configuration` options, the Esbonio VSCode extension provides the following options.

.. esbonio:config:: esbonio.server.enabled
   :scope: global
   :type: boolean

   A flag that can be used to completely disable the language server, if required.

.. esbonio:config:: esbonio.server.enabledInPyFiles (boolean)
   :scope: global
   :type: boolean

   A flag that controls if the language server is enabled in Python files.

.. esbonio:config:: esbonio.server.excludedModules
   :scope: global
   :type: string[]

   A list of :ref:`lsp-extension-modules` to exclude from the server.

.. esbonio:config:: esbonio.server.includedModules
   :scope: global
   :type: string[]

   A list of additional :ref:`lsp-extension-modules` to include in the server.

.. esbonio:config:: esbonio.server.pythonPath
   :scope: global
   :type: string

   If the official `Python Extension`_ is available the extension will use the same
   Python environment as you have configured for your workspace. However, if you wish
   to use a different environment or do not have the Python extension installed this
   option can be set to tell the extension which environment to use.

   Currently accepted values include:

   - ``/path/to/python/`` - An absolute path
   - ``${workspaceRoot}/../venv/bin/python`` - A path relative to the root of your workspace
   - ``${workspaceFolder}/../venv/bin/python`` -  Same as ``${workspaceRoot}``, placeholder for true multi-root workspace support.

.. _Python Extension: https://marketplace.visualstudio.com/items?itemName=ms-python.python


Commands
--------

The Esbonio VSCode extension also provides a number of commands accessible through VSCode's command
palette (:kbd:`Ctrl+Shift+P`).

``esbonio.preview.open``
   This will open a webview in the current editor window showing the latest html build of the
   document being edited.

``esbonio.preview.openSide``
   Much like the ``esbonio.preview.open`` command, this will open a webview showing the latest build
   for the current document but to the side of the editor window. Additionally, as you change
   between source files the preview will automatically update to show the page you are
   currently working on.

``esbonio.sphinx.copyBuildCommand``
   Copy the server's current ``sphinx-build`` command to the clipboard.

``esbonio.sphinx.setBuildCommand``
   Prompts for a set of ``sphinx-build`` arguments and updates the project's configuration accordingly.

``esbonio.server.restart``
   This will kill and restart the language server
