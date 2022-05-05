Esbonio
=======

.. rubric:: esbonio -- (v.) to explain

Esbonio aims to make it easier to work with `reStructuredText`_ tools such as
`Sphinx`_ by providing a `Language Server`_ to enhance your editing experience.

Language Server
---------------

Here is a quick summary of the features implemented by the language server.

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


- See the :ref:`lsp_getting_started` guide for details on how to get up and
  running.

.. - TODO: Extending
.. - TODO: Contributing.

.. toctree::
   :glob:
   :caption: Language Server
   :hidden:
   :maxdepth: 2

   lsp/getting-started
   lsp/advanced-usage
   lsp/extending
   lsp/how-to
   changelog

Sphinx Extensions
-----------------

In addition to the language server, the Esbonio project provides a number of
Sphinx extensions.

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
