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
