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

Previously, it was recommended to install ``esbonio`` as a development dependency for each project you wished to use with.
This was because ``esbonio`` would run Sphinx as part of its own process and therefore need access to your project's dependencies.

In ``v1.x`` Sphinx is now run in a separate process so this is no longer necessary, in fact, it's recommended you remove it from your project specific environments::

   (env) $ pip uninstall esbonio

Instead, you can now have a single, global installation that is reused across projects.
It's recommended that you use `pipx <https://pipx.pypa.io/stable/>`__ to manage this installation for you::

   $ pipx install esbonio   # Installs esbonio globally in an isolated environment
   $ pipx upgrade esbonio   # Upgrade esbonio and its dependencies

.. note::

   If you use the Esbonio VSCode extension, the language server is automatically included as part of the extension itself, no separate installation required!

Configuration Changes
---------------------

.. tip::

   With the release of ``v1.x``, Esbonio's configuration system has been overhauled, see :ref:`lsp-configuration` for all of the available configuration options and methods.

While ``esbonio`` can now be installed globally, it still needs access to your project's development environment in order launch Sphinx correctly.
This means the two most imporant configuration values are

- :esbonio:conf:`esbonio.sphinx.pythonCommand`: For telling ``esbonio`` the command it needs to run in order to use the correct Python environment.
- :esbonio:conf:`esbonio.sphinx.buildCommand`: For telling ``esbonio`` the ``sphinx-build`` command you use to build your documentation. This is so that the server invoke Sphinx with the correct arguments.

The following table outlines the configuration options that have been removed in ``v1.x`` and what their correpsonding replacement is

+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| Removed Option                          | Replacement                                     | Notes                                                        |
+=========================================+=================================================+==============================================================+
| - ``esbonio.sphinx.builderName``        | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Pass ``-b <builderName> <srcDir> <buildDir>`` to             |
| - ``esbonio.sphinx.srcDir``             |                                                 | ``sphinx-build``                                             |
| - ``esbonio.sphinx.buildDir``           |                                                 |                                                              |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.confDir``              | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-c <confDir>``                                         |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.doctreeDir``           | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-d <doctreeDir>``                                      |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.forceFullBuild``       | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-E``                                                   |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.keepGoing``            | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``--keep-going``                                         |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.makeMode``             | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Pass ``-M <builderName> <srcDir> <buildDir>`` to             |
|                                         |                                                 | ``sphinx-build``                                             |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.numJobs``              | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-j <numJobs>``                                         |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.quiet``                | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-q``                                                   |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.tags``                 | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-t``                                                   |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.verbosity``            | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-v``                                                   |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.sphinx.warningIsError``       | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-W``                                                   |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| - ``esbonio.server.hideSphinxOutput``   | :esbonio:conf:`esbonio.sphinx.buildCommand`     | Use ``-Q``                                                   |
| - ``esbonio.sphinx.silent``             |                                                 |                                                              |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.server.logLevel``             | :esbonio:conf:`esbonio.logging.level`           |                                                              |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.server.logFilter``            | :esbonio:conf:`esbonio.logging.config`          |                                                              |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| ``esbonio.server.enabledInPyFiles``     | :esbonio:conf:`esbonio.server.documentSelector` | VSCode only                                                  |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
| - ``esbonio.server.installBehavior``    | N/A                                             | VSCode only, no longer required.                             |
| - ``esbonio.server.updateBehavior``     |                                                 |                                                              |
| - ``esbonio.server.updateFrequency``    |                                                 |                                                              |
+-----------------------------------------+-------------------------------------------------+--------------------------------------------------------------+
