
.. note::

   This guide was written using Kate ``v22.12.1``

#. Open Kate's settings through the :guilabel:`Settings -> Configure Kate...` menu, or with the :kbd:`Ctrl+Shift+,` shortcut.

#. Select the :guilabel:`Plugins` section on the left hand side, find the :guilabel:`LSP Client` plugin and ensure that it's checked.

   .. figure:: /images/kate-plugin-settings.png
      :align: center
      :width: 80%

      Kate's :guilabel:`Plugins` settings.

#. With the LSP Client enabled, open the :guilabel:`LSP Client` configuration section and select the :guilabel:`User Server Settings` tab.

#. This should open up a text box where you can enter some JSON to tell Kate how and when to start the language server.

   .. code-block:: json

      {
        "servers": {
          "rst": {
            "command": ["python", "-m", "esbonio"],
            "initializationOptions": {
              "sphinx": { },
              "server": {
                "completion": {
                  "preferredInsertBehavior": "insert"
                }
              }
            },
            "rootIndicationFileNames": ["conf.py"],
            "highlightingModeRegex": "^reStructuredText$"
          }
        }
      }

   For best results, we recommend you set :confval:`server.completion.preferredInsertBehavior (string)` to ``insert``, see the section on :ref:`lsp-configuration` for details  on all the available options.

   For more details on Kate's LSP client see the `project's <https://docs.kde.org/stable5/en/kate/kate/kate-application-plugin-lspclient.html>`__ documentation.

#. Once you're happy with your configuration be sure to hit the :guilabel:`Save` button for
   it to take effect!

   .. figure:: /images/kate-lsp-settings.png
      :align: center
      :width: 80%

      Kate's :guilabel:`LSP Client` settings with an example Esbonio config.

.. note::

   **Python Environments**

   In order for the language server to function correctly it needs to be installed into and
   run from the same Python environment as the one used to build your documentation. In order
   for Kate to correctly determine the right Python environment to use, you can either

   - Modify the ``command`` array in your LSP Config to use the full path to the
     correct Python, or
   - Start Kate from the terminal with the correct Python environment activated::

      (.env) $ kate
