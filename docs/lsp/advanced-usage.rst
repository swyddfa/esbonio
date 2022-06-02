.. _lsp-advanced:

Advanced Usage
==============

The :doc:`/lsp/getting-started` guide should contain all you need to get up and running with your
editor of choice. However there may come a time when you will want to enable/disable certain
functionality or use a different server entirely.

**Wait.. there are different servers?**

Yes there are!

Due to the extensible nature of Sphinx and reStructuredText, the ``esbonio`` python package
is actually a framework for building reStructuredText language servers. It just so happens
that it also comes with a default implementation that works well for Sphinx projects (see
the section on :doc:`/lsp/extending` if you want to know more)

However, all that we need to know for the moment is the concept of startup modules.

.. _lsp-startup-mods:

Startup Modules
---------------

A startup module is any python module (or script) that results in a running language server.
The following startup modules are included with the ``esbonio`` python package.

.. startmod:: esbonio

   The default startup module you are probably already familiar with.
   It is in fact just an alias for the :startmod:`esbonio.lsp.sphinx` startup module.

   ..   .. cli-help:: esbonio.__main__

.. startmod:: esbonio.lsp.rst

   A "vanilla" reStructuedText language server for use with docutils projects.

   ..   .. cli-help:: esbonio.lsp.rst

.. startmod:: esbonio.lsp.sphinx

   A language server tailored for use with Sphinx projects.

   .. .. cli-help:: esbonio.lsp.sphinx


Extension Modules
-----------------

Inspired by the way Sphinx extensions work, functionality is added to a language server through a list of python modules with each module contributing some features.

Below is the list of modules loaded by default for each of the provided servers.

.. relevant-to:: Startup Module

   esbonio
      .. literalinclude:: ../../lib/esbonio/esbonio/lsp/sphinx/__init__.py
         :language: python
         :start-at: DEFAULT_MODULES
         :end-at: ]

   esbonio.lsp.rst
      .. literalinclude:: ../../lib/esbonio/esbonio/lsp/rst/__init__.py
         :language: python
         :start-at: DEFAULT_MODULES
         :end-at: ]

   esbonio.lsp.sphinx
      .. literalinclude:: ../../lib/esbonio/esbonio/lsp/sphinx/__init__.py
         :language: python
         :start-at: DEFAULT_MODULES
         :end-at: ]

In addition to the modules enabled by default, the following modules are provided and can be
enabled if you wish.

.. extmod:: esbonio.lsp.spelling

   **Experimental**

   Basic spell checking, with errors reported as diagnostics and corrections suggested as code actions.
   Currently only available for English and can be confused by reStructuredText syntax.

Commands
--------

The bundled language servers offer some commands that can be invoked from a language client using
a :lsp:`workspace/executeCommand` request.

.. relevant-to:: Startup Module

   esbonio
      .. include:: ./advanced/_esbonio.lsp.sphinx_commands.rst

   esbonio.lsp.rst
      ``esbonio.server.configuration``
         Returns the server's current configuration.

         .. code-block:: json

            {
              "server": {
                "logLevel": "debug",
                "logFilter": [],
                "hideSphinxOutput": false
              }
            }

      ``esbonio.sever.preview``
         Currently a placeholder.

   esbonio.lsp.sphinx
      .. include:: ./advanced/_esbonio.lsp.sphinx_commands.rst

Notifications
-------------

The bundled language servers also emit custom notifications that language clients
can use to react to events happening within the server.

.. relevant-to:: Startup Module

   esbonio
      .. include:: ./advanced/_esbonio.lsp.sphinx_notifications.rst

   esbonio.lsp.rst
      Currently this server implements no custom notifications.

   esbonio.lsp.sphinx
      .. include:: ./advanced/_esbonio.lsp.sphinx_notifications.rst
