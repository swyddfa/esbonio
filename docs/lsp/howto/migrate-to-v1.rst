.. _lsp-v1-migration:

How To Migrate to v1
====================

.. note::

   Since v1.0 is still under development, some features from ``0.x`` may still be missing.
   Also the details in this guide may change over time.

This guide covers the breaking changes between the ``v0.x`` and ``v1.x`` versions of the language server and how to adapt to them.

.. highlight:: console

Installation Changes
--------------------

Previously, you would have had to install ``esbonio`` as a development dependency for every project you wished to use it in.
In ``v1.x`` this is no longer necessary, in fact, it's recommended you remove it from all of your project specific environments::

   (env) $ pip uninstall esbonio

Instead, you should now have a single, global installation that can be reused across projects.
We recommend that you use `pipx <https://pipx.pypa.io/stable/>`__ to manage this installation for you::

   $ pipx install esbonio   # Installs esbonio globally in an isolated environment
   $ pipx upgrade esbonio   # Upgrade esbonio and its dependencies

.. note::

   If you use the Esbonio VSCode extension, the language server is automatically included as part of the extension itself, no separate installation required!

Configuration Changes
---------------------

.. tip::

   With the release of ``v1.x``, Esbonio's configuration system has been overhauled, see :ref:`lsp-configuration` for all of the available configuration options and methods.

While ``esbonio`` can now be installed globally, it still needs access to your project's development environment in order to properly understand it.
This means the two most imporant configuration values are

- :esbonio:conf:`esbonio.sphinx.pythonCommand`: For telling ``esbonio`` the command it needs to run in order to use the correct Python environment.
- :esbonio:conf:`esbonio.sphinx.buildCommand`: For telling ``esbonio`` the ``sphinx-build`` command you use to build your documentation. This is so that the server invoke Sphinx with the correct arguments.

The following table outlines the configuration options that have been removed in ``v1.x`` and what their correpsonding replacement is

+-----------------------------------------+-------------------------------------------------+-------------+
| Removed Option                          | Replacement                                     | Notes       |
+=========================================+=================================================+=============+
| - ``esbonio.server.hideSphinxOutput``   | :esbonio:conf:`esbonio.sphinx.buildCommand`     |             |
| - ``esbonio.sphinx.buildDir``           |                                                 |             |
| - ``esbonio.sphinx.builderName``        |                                                 |             |
| - ``esbonio.sphinx.confDir``            |                                                 |             |
| - ``esbonio.sphinx.doctreeDir``         |                                                 |             |
| - ``esbonio.sphinx.forceFullBuild``     |                                                 |             |
| - ``esbonio.sphinx.keepGoing``          |                                                 |             |
| - ``esbonio.sphinx.makeMode``           |                                                 |             |
| - ``esbonio.sphinx.numJobs``            |                                                 |             |
| - ``esbonio.sphinx.quiet``              |                                                 |             |
| - ``esbonio.sphinx.silent``             |                                                 |             |
| - ``esbonio.sphinx.srcDir``             |                                                 |             |
| - ``esbonio.sphinx.tags``               |                                                 |             |
| - ``esbonio.sphinx.verbosity``          |                                                 |             |
| - ``esbonio.sphinx.warningIsError``     |                                                 |             |
+-----------------------------------------+-------------------------------------------------+-------------+
| ``esbonio.server.logLevel``             | :esbonio:conf:`esbonio.logging.level`           |             |
+-----------------------------------------+-------------------------------------------------+-------------+
| ``esbonio.server.logFilter``            | :esbonio:conf:`esbonio.logging.config`          |             |
+-----------------------------------------+-------------------------------------------------+-------------+
| ``esbonio.server.enabledInPyFiles``     | :esbonio:conf:`esbonio.server.documentSelector` | VSCode only |
+-----------------------------------------+-------------------------------------------------+-------------+
| - ``esbonio.server.installBehavior``    | N/A                                             | VSCode only,|
| - ``esbonio.server.updateBehavior``     |                                                 | no longer   |
| - ``esbonio.server.updateFrequency``    |                                                 | required.   |
+-----------------------------------------+-------------------------------------------------+-------------+
