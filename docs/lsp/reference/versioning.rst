Versioning
==========

The Esbonio language server uses version numbers that adhere to :pep:`440` with a ``major.minor.micro`` scheme.

- The ``major`` version number is incremented whenever breaking changes in **features that have been declared stable** are introduced.

- The ``minor`` version number is incremented whenever a release contains new features or enhancements to existing features.

- The ``micro`` version number is incremented whenever a relase contains only bug fixes.

As a general rule, a major release should be expected around each major release of Python and Sphinx so that Esbonio can keep pace with the rest of the ecosystem. (Just note that this is a small project, so there will likely be a lag!).

**Stable Features**

The following aspects of the language server are considered stable.
Incompatible changes to the list below should be accompanied with a ``major`` version bump.

- :ref:`lsp-sphinx-support`
- :ref:`lsp-python-support`
- The server's command line interface and associated flags
- :ref:`lsp-configuration` options and their associated defaults

**Unstable Features**

By definition, "everything else" should be considered unstable.
However, there are some aspects that deserve a special mention.

- :ref:`Extension APIs <lsp-extending>`.

  The internals of the language server are still relatively immature, you can expect breaking changes to any APIs as part of regular releases.


.. _lsp-sphinx-support:

Supported Sphinx Versions
-------------------------

Each major version of Esbonio will support the current and previous two major versions of Sphinx.
For example

- Esbonio ``1.x`` has support for Sphinx versions ``8.x``, ``7.x`` and ``6.x``.
- Esbonio ``2.x`` will support Sphinx versions ``9.x``, ``8.x`` and ``7.x``.

.. _lsp-python-support:

Supported Python Versions
-------------------------

Each major version of Esbonio will support all `actively supported <https://devguide.python.org/versions/>`__ Python versions, *unless* that version is not supported by any supported version of Sphinx.
