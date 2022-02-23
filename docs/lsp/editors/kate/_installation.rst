Kate's LSP client is provided via a plugin that needs to be enabled if you're using
it for the first time.

1. Open Kate's settings through the :guilabel:`Settings -> Configure Kate...` menu,
   or with the :kbd:`Ctrl+Shift+,` shortcut.

2. Select the :guilabel:`Plugins` section on the left hand side find the
   :guilabel:`LSP Client` plugin and ensure that it's checked.

   .. figure:: /images/kate-plugin-settings.png
      :align: center
      :width: 80%

      Kate's :guilabel:`Plugins` settings.

3. Once checked a new :guilabel:`LSP Client` section should appear at the bottom of the
   list. Open it and select the :guilabel:`User Server Settings` tab.

4. This should open up a text box where you can enter some JSON to tell Kate how and
   when to start the language server.

   .. code-block:: json

      {
        "servers": {
          "rst": {
            "command": ["python", "-m", "esbonio"],
            "initializationOptions": {
              "sphinx": {
                "srcDir": "",
                "confDir": ""
              },
              "server": {}
            },
            "rootIndicationFileNames": ["conf.py"],
            "highlightingModeRegex": "^reStructuredText$"
          }
        }
      }

   For more details general LSP configuration have a look at `Kate's LSP Client`_
   documentation.

5. Once you're happy with your configuration be sure to hit the :guilabel:`Apply` button for
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

.. _Kate's LSP Client: https://docs.kde.org/stable5/en/kate/kate/kate-application-plugin-lspclient.html
