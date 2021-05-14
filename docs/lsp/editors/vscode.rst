.. _editor_itegration_vscode:

VSCode
======

.. figure:: /_static/images/vscode-screenshot.png
   :align: center
   :width: 80%

   The VSCode extension editing this page


Integration with the `VSCode`_ editor is provided via the `Esbonio`_ extension.


Configuration
"""""""""""""

In addition to the following options the VSCode extension also supports
:ref:`editor_integration_config` options.

``esbonio.server.pythonPath`` (string)
   If the official `Python Extension`_ is available the extension will use the same
   Python environment as you have configured for your workspace. However, if you wish
   to use a different environment or do not have the Python extension installed this
   option can be set to tell the extension which environment to use.

``esbonio.server.installBehavior`` (string)
   The VSCode extension can manage the installation of the language server for you.
   If the language server is missing from your current environment the extension will prompt
   by default to check if you want it to perform the installation. If you don't like this
   behavior you can use this option to change it, the following values are valid

   - ``nothing`` - Don't attempt to install the language server if it's missing
   - ``prompt`` (default) - Ask for confirmation before installing the server
   - ``automatic`` - Never ask for confirmation, the language server will be installed
     automatically in new environments

``esbonio.server.updateFrequency`` (string)
   The VSCode extension can also automatically install updates to the language server
   as they are released. By default the extension will check on start up once a week,
   alternatively you can set this setting to one of the following values

   - ``never`` - Never check for updates. Though you can still trigger an update
     manually if you wish.
   - ``monthly`` - Check for updates once a month
   - ``weekly`` - Check for updates once a week
   - ``daily`` - Check for updates once a day

``esbonio.server.updateBehavior`` (string)
   If an update is detected through one of the extension's automated checks this option
   controls what the extension does next. By default the extension will automatically
   install it **unless** it is a major update (e.g ``1.x.y`` -> ``2.0.0``). The following
   options are available

   - ``promptAlways`` - Always ask for confirmation before applying updates
   - ``promptMajor`` - Only ask for confirmation on major updates, minor versions will be
     installed automatically
   - ``automatic`` - Never ask for confirmation, updates will always be installed.

Commands
""""""""

The VSCode extension provides a number of commands accessible through VSCode's command
palette (:kbd:`Ctrl+Shift+P`) and in some cases via a default keybinding.

Insert Inline Link - ``esbonio.insert.inlineLink`` - :kbd:`Alt+l`
   This inserts an inline link into the current document, for example::

      `Sphinx <https://www.sphinx-doc.org/en/master>`_ is a fantastic
      documentation tool

   Upon triggering the command vscode will first prompt you for the URL you wish to
   link to followed by the label you want the reader to see. It will then insert the link
   into the document at the position of your cursor.

   .. tip::

      If you select some text before triggering the command, the text you selected will be
      used as the link's label.

Insert Link - ``esbonio.insert.link`` - :kbd:`Alt+Shift+l`
   This inserts a "named link" into the current document, for example::

      `Sphinx`_ is a fantastic documentation tool

      .. _Sphinx: https://www.sphinx-doc.org/en/master

   Upon triggering the command vscode will first prompt you for the URL you wish to
   link to followed by the label you want the reader to see. It will then insert both
   the definition at the end of the document and the reference at the position of your
   cursor.

   .. tip::

      If you select some text before triggering the command, the text you selected will be
      used as the link's label.

Install Language Server - ``esbonio.server.install``
   This can be used to manually install the language server into the current environment

Restart Language Server - ``esbonio.server.restart``
   The can be used to kill and restart the language server

Update Language Server - ``esbonio.server.update``
   This can be used to manually trigger an update to the language server



Changelog
"""""""""

.. include:: ../../../code/CHANGES.rst

.. _VSCode: https://code.visualstudio.com/
.. _Esbonio: https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio
.. _Python Extension: https://marketplace.visualstudio.com/items?itemName=ms-python.python
