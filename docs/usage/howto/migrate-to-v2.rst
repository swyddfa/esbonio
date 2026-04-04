.. _lsp-v2-migration:

How To Migrate to v2
====================

This guide covers the breaking changes between the ``v1.x`` and ``v2.x`` versions of the language server and how to adapt to them.

Sphinx v6 No Longer Supported
-----------------------------

Inline with the :ref:`about-versioning` policy, while Esbonio v2 adds support for Sphinx v9, support for Sphinx v6 has been removed.

Configuration Changes
---------------------

The default values for the following configuration options have been changed.

- :esbonio:conf:`esbonio.logging.level` now defaults to ``info``
- :esbonio:conf:`esbonio.server.completion.preferredInsertBehavior` now defaults to ``insert``
