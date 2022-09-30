.. _lsp-extending:

Extending
=========

In order to support the extensible nature of reStructuredText and Sphinx, Esbonio itself is structured so that it can be easily extended.
This section of the documentation outlines the server's architecture and how you can write your own extensions.

.. toctree::
   :maxdepth: 1

   extending/directives
   extending/api-reference

.. _lsp_architecture:

Architecture
------------

.. include:: ./_architecture.rst

.. glossary::

   Language Server
      A language server is a subclass of the ``LanguageServer`` class provided by the `pygls`_ library.

      In Esbonio, all the features you would typically associate with a language server, e.g. completions are not actually implemented by the language server.
      These features are provided through a number of "language features" (see below).
      Instead a language server acts a container for all the active language features and provides an API they can use to query aspects of the environment.

      Esbonio currently provides two language servers

      - :class:`~esbonio.lsp.rst.RstLanguageServer`: Base language server, meant for "vanilla" docutils projects.
      - :class:`~esbonio.lsp.sphinx.SphinxLanguageServer` Language server, specialising in Sphinx projects.

   Language Feature
      Language features are subclasses of :class:`~esbonio.lsp.rst.LanguageFeature`.
      They are typically based on a single aspect of reStructuredText (e.g. :class:`~esbonio.lsp.roles.Roles`).

      Language Features (where it makes sense) should be server agnostic, that way the same features can be reused across different envrionments.

   Engine
      For lack of a better name... an "engine" is responsible for mapping messages from the LSP Protocol into function calls within the language server.
      Unlike the other components of the architecture, an "engine" isn't formally defined and there is no API to implement.
      Instead it's just the term used to refer to all the ``@server.feature()`` handlers that define how LSP messages should be handled.

      Currently we provide just a single "engine" :func:`~esbonio.lsp.create_language_server`.
      As an example, here is how it handles ``textDocument/completion`` requests.

      .. literalinclude:: ../../lib/esbonio/esbonio/lsp/__init__.py
         :language: python
         :dedent:
         :start-after: # <engine-example>
         :end-before: # </engine-example>

      There is nothing in Esbonio that would prevent you from writing your own if you so desired.

   Extension Module
      Ordinary Python modules are used to group related functionality together.
      Taking inspiration from how Sphinx is architected, language servers are assembled by passing the list of modules to load to the :func:`~esbonio.lsp.create_language_server`.
      This assembly process calls any functions with the name ``esbonio_setup`` allowing for ``LanguageFeatures`` to be configured and loaded into the server.

   Startup Module
      As mentioned above, language servers are assembled and this is done inside a startup module.
      A startup module in Esbonio is any Python script or module runnable by a ``python -m <modulename>`` command that results in a running language server.
      A good use case for a custom entry point would be starting up a language server instance pre configured with all the extensions required by your project.


.. _pygls:  https://pygls.readthedocs.io/en/latest/index.html
