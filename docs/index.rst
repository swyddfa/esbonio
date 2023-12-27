Esbonio
=======

.. rubric:: esbonio -- (v.) to explain

Esbonio is a `Language Server`_ for `Sphinx`_ documentation projects.

Esbonio aids the writing process by resolving references, providing completion suggestions and highlighting errors.
It ensures your local build is always up to date, allowing you to preview your changes in (almost!) real-time.
The server itself can even be extended to better suit the needs of your project.

The primary goal of Esbonio is to reduce the friction that comes from trying to remember the specifics of a markup language, so that you can focus on your content and not your tooling.

.. grid:: 2
   :gutter: 1

   .. grid-item-card:: Getting Started
      :text-align: center
      :link: lsp-getting-started
      :link-type: ref

      Using Esbonio for the first time within VSCode.

   .. grid-item-card:: How-To Guides
      :text-align: center

      Step-by-step guides on integrating Esbonio with other text editors.

   .. grid-item-card:: Reference
      :text-align: center
      :link: lsp-reference
      :link-type: ref

      Configuration options, API documentation, architecture diagrams and more.

   .. grid-item-card:: Extending
      :text-align: center
      :link: lsp-extending
      :link-type: ref

      Documentation on extendining the Esbonio language server


Language Server
---------------

Below are some of the features provided by the language server.

.. collection:: features

   .. collection-item:: Completion

      The language server implements :lsp:`textDocument/completion` and can
      offer suggestions in a variety of contexts.

      .. figure:: ../resources/images/completion-demo.gif
         :align: center
         :target: /_images/completion-demo.gif

   .. collection-item:: Definition

      The language server implements :lsp:`textDocument/definition` to provide the
      location of items referenced by certain roles. Currently only the ``:ref:``
      and ``:doc:`` roles are supported.

      .. figure:: ../resources/images/definition-demo.gif
         :align: center
         :target: /_images/definition-demo.gif

   .. collection-item:: Diagnostics

      The language server implements :lsp:`textDocument/publishDiagnostics` to
      report errors/warnings enountered during a build.

      .. figure:: ../resources/images/diagnostic-sphinx-errors-demo.png
         :align: center
         :target: /_images/diagnostic-sphinx-errors-demo.png

   .. collection-item:: Document Links

      The language server implements :lsp:`textDocument/documentLink` to make references to other files "Ctrl + Clickable"

      .. figure:: ../resources/images/document-links-demo.png
         :align: center
         :target: /_images/document-links-demo.png

   .. collection-item:: Document Symbols

      The language server implements :lsp:`textDocument/documentSymbol` which
      powers features like the "Outline" view in VSCode.

      .. figure:: ../resources/images/document-symbols-demo.png
         :align: center
         :target: /_images/document-symbols-demo.png

   .. collection-item:: Hover

      The language server implements :lsp:`textDocument/hover` to provide easy access to documentation for roles and directives.

      .. figure:: ../resources/images/hover-demo.png
         :align: center
         :target: /_images/hover-demo.png

   .. collection-item:: Implementation

      The language server implements :lsp:`textDocument/implementation` so you can easily find the implementation of a given role or directive.

      .. figure:: ../resources/images/implementation-demo.gif
         :align: center
         :target: /_images/implementation-demo.gif

.. toctree::
   :glob:
   :caption: Language Server
   :hidden:
   :maxdepth: 2

   lsp/getting-started
   lsp/advanced-usage
   lsp/how-to
   lsp/extending
   lsp/howto
   lsp/reference
   changelog

Sphinx Extensions
-----------------

In addition to the language server, the Esbonio project provides a number of
Sphinx extensions.

- :doc:`/extensions/relevant_to`: Swap out sections of an article based on a chosen subject.
- :doc:`/extensions/tutorial`: Export tutorial articles as `Jupyter Notebooks`_

.. toctree::
   :glob:
   :maxdepth: 1
   :caption: Sphinx Extensions
   :hidden:

   extensions/*


.. toctree::
   :glob:
   :maxdepth: 2
   :hidden:
   :caption: Contributing

   contributing/*

.. _Language Server: https://langserver.org/
.. _Jupyter Notebooks: https://jupyter.org/
.. _reStructuredText: https://docutils.sourceforge.io/rst.html
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _VSCode: https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio
