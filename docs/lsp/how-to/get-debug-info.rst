How To: Get Debug Information
=============================

In its default configuration the language server doesn't give you much information, you get Sphinx's build output and not much else.
Depending on your needs you may find one of the following options useful.

Enable Debug Logging
--------------------

The simplest way to get more information is to set the :confval:`server.logLevel (string)` option to ``debug``.
Additional messages from the language server will be sent to your language client as :lsp:`window/logMessage` messages.

Capture All Messages
--------------------

If you are using one of the VSCode extensions you can set the ``esbonio.trace.server`` option to ``verbose``.
This will print all LSP message bodies sent to/from the client in the ``Output`` window.

**Note:** This will generate a *lot* of output.

Capture All Output
------------------

.. important::

   This option requires the ``lsp-devtools`` package be installed in the same Python environment as the ``esbonio`` language server::

      $ pip install lsp-devtools

Alternatively you can capture **everything** sent to/from the language server in a text file ``lsp.log`` by using one of the following debug :ref:`lsp-startup-mods`

.. startmod:: esbonio.lsp.rst._record

   Exactly the same as :startmod:`esbonio.lsp.rst`, but with output capture enabled.

.. startmod:: esbonio.lsp.sphinx._record

   Exaclty the same as :startmod:`esbonio.lsp.sphinx` but with output capture enabled.
