Sublime Text
============

Installation
------------

.. highlight:: none

Basic configuration for the language server is provided through the
`LSP <https://github.com/sublimelsp/LSP>`__ plugin

.. literalinclude:: ./editors/sublimetext-lsp/LSP.sublime-settings
   :language: json
   :start-at: {

The server language executable can be overridden per project basis; refer to
`Sublime Text Projects documentation <https://www.sublimetext.com/docs/projects.html>`_.


Alternatively, you can change the default command to launch the language sever with a particular
interpreter

.. code-block:: json

   "clients": {
       "esbonio": {
           "enabled": true,
           "command": [
               "/path/to/virtualenv/bin/python",
               "-m",
               "esbonio"
           ],


Configuration
-------------

The language server's configuration options are passed as
``initializationOptions`` during the server's setup e.g.

.. code:: json

   {
       "clients": {
           "esbonio": {
               "enabled": true,
               "command": ["esbonio"],
               "selector": "text.restructuredtext",
               "initializationOptions": {
                   "server": {
                       "logLevel": "debug"
                   },
                   "sphinx": {
                     "confDir": "/path/to/docs"
                     "srcDir": "${confDir}/../docs-src"
                   }
               }
           }
       }
   }

Here are all the options supported by the server.

Examples
--------

To try the example configuration on your machine.

#. Ensure you have `Package Control <https://packagecontrol.io>`_
   installed.
#. Install `LSP <https://packagecontrol.io/packages/LSP>`__ package.
#. Open Command Palette and choose `Preferences: LSP Settings`
#. Copy the content of :download:`LSP.sublime-settings
   <sublime/LSP.sublime-settings>` to the settings file.


Troubleshooting
---------------

Refer to the troubleshooting guide of `LSP <https://lsp.sublimetext.io/troubleshooting/>`__.
