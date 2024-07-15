.. _integrate-kate:

How To Integrate Esbonio with Kate
==================================

.. figure:: /images/kate-screenshot.png
   :align: center
   :target: /_images/kate-screenshot.png

   Using the esbonio language server from within Kate


Installation
------------

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
            "settings": {
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

   For best results, we recommend you set :esbonio:conf:`esbonio.server.completion.preferredInsertBehavior` to ``insert``, see the section on :ref:`lsp-configuration` for details  on all the available options.

   For more details on Kate's LSP client see the `project's <https://docs.kde.org/stable5/en/kate/kate/kate-application-plugin-lspclient.html>`__ documentation.

#. Once you're happy with your configuration be sure to hit the :guilabel:`Save` button for
   it to take effect!

   .. figure:: /images/kate-lsp-settings.png
      :align: center
      :width: 80%

      Kate's :guilabel:`LSP Client` settings with an example Esbonio config.

Configuration
-------------

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
