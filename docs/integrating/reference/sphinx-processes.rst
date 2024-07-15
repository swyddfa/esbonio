Sphinx Process Management
=========================

The language server provides additional notifications and commands that the client can use to provide greater insight and control over the Sphinx sub-processes mananged by ``esbonio``

Life-Cycle Notifications
------------------------

The following notifications will be emitted following during the life-cycle of a Sphinx sub-process

.. currentmodule:: esbonio.server.features.sphinx_manager.manager

.. autoclass:: ClientCreatedNotification
   :members:

.. autoclass:: AppCreatedNotification
   :members:

.. autoclass:: ClientErroredNotification
   :members:

.. autoclass:: ClientDestroyedNotification
   :members:

Commands
--------

The server offers the following commands for controlling the underlying Sphinx processes.
They are invoked using an :lsp:`workspace/executeCommand` request

.. esbonio:command:: esbonio.sphinx.restart

   Restart the given Sphinx client(s).
   This command accepts a list of objects of the following form

   .. code-block:: json

      {"id": "a0a5a856-d4ec-4c45-8461-78748ddbd06f"}

   Where each ``id`` corresponds to a Sphinx Client.
