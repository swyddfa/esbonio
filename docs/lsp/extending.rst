.. _lsp-extending:

Extending
=========

As mentioned in the :ref:`lsp-advanced` section, ``esbonio`` is actually framework for building reStructuredText based language servers.
It just so happens that ``esbonio`` also ships with an implementation that works well for Sphinx projects.

This means that it's possible to extend the default implementation to add support for your own Sphinx extensions or even build a new server entirely!

However, before diving into the details on how you can start building on this framework it's worth giving you a quick tour of the architecture to hopefully paint a picture on the various components and how they relate to each other.
Once we've covered the architecture, you should be in a better position to decide what kind of extension best suits your needs.

.. warning::

   It is still early days and the extension APIs described here are **not** stable and may be subject to change over time, that said we will try to avoid unecessary breakages.

   The flip side of this of course is that you have the opporunity to influence the design of the extension API before it is declared stable in ``v1.0`` so if you think something should be added/changed then please `get in touch! <https://github.com/swyddfa/esbonio/issues/new/choose>`_

.. _lsp_architecture:

Architecture
------------

.. include:: extending/_architecture.rst

A typical request-response cycle goes something like the following.

#. A language client sends a request over :obj:`stdin <python:sys.stdin>` to the Python process running the server.

#. The :term:`Engine` translates the request into function calls within the language server.

#. The :term:`Language Server` manages the environment (e.g. Sphinx application lifecycle) and routes requests to the appropriate language features.

#. One or more :term:`Language Features <Language Feature>` produce a result.
   Some features (like :class:`~esbonio.lsp.roles.Roles` and :class:`~esbonio.lsp.directives.Directives`) may call out to a number of :term:`Providers <Provider>` during this process.

#. The language server aggregates the results from each of the language features, preparing the response to send back to the client.

#. The engine sends this response back to the client over :obj:`stdout <python:sys.stdout>`.

Extension Points
----------------

This section dives into each of the components introduced above outlining how you can make use of them in your own extensions.
The components are listed from the most specific to the most generic.

.. glossary::

   Provider
      A number of :term:`Language Features <Language Feature>` have the concept of a "provider".

      A provider can be used to extend the functionality of an existing language feature, for example

      However, a pattern commonly used in Esbonio is allowing multiple "providers" to be registered with a ``LanguageFeature``, extending its functionality in some way.
      The API that a provider must implement varies and is defined by the language feature that uses it. An example of such a provider it the :class:`~esbonio.lsp.directives.ArgumentCompletion`
      provider which allows extensions to provide completion suggestions for directive arguments.

   Language Feature
      Language features are subclasses of :class:`~esbonio.lsp.rst.LanguageFeature`.
      They are typically based on a single aspect of reStructuredText (e.g. :class:`~esbonio.lsp.roles.Roles`).

      Language Features (where it makes sense) should be server agnostic, that way the same features can be reused across different envrionments.

   Language Server
      A language server is a subclass of the ``LanguageServer`` class provided by the `pygls`_ library.

      In Esbonio, all the features you would typically associate with a language server, e.g. completions are not actually implemented by the language server.
      These features are provided through a number of "language features" (see below).
      Instead a language server acts a container for all the active language features and provides an API they can use to query aspects of the environment.

      Esbonio currently provides two language servers

      - :class:`~esbonio.lsp.rst.RstLanguageServer`: Base language server, meant for vanilla docutils projects.
      - :class:`~esbonio.lsp.sphinx.SphinxLanguageServer` Language server, specialising in Sphinx projects.

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

.. toctree::
   :maxdepth: 1

   extending/your-first-extension
   extending/api-reference


.. _pygls:  https://pygls.readthedocs.io/en/latest/index.html
