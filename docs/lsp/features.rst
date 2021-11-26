Features
========

This page contains a quick overview of the features offered by the Language
Server

Completion
----------

The language server implements :lsp:`textDocument/completion` and can offer suggestions
in a variety of contexts.

.. figure:: ../../resources/images/completion-demo.gif
   :align: center

Document Symbols
----------------

The language server implements :lsp:`textDocument/documentSymbol` which powers
features like the "Outline" view in VSCode.

.. figure:: ../../resources/images/document-symbols-demo.png
   :align: center

Diagnostics
-----------

Using :lsp:`textDocument/publishDiagnostics` the language server is able to report Sphinx
errors that are reported during builds.

.. figure:: ../../resources/images/diagnostic-sphinx-errors-demo.png
   :align: center

   Example diagnostic messages from Sphinx

Goto Definition
---------------

The language server implements :lsp:`textDocument/definition`  to provide the location of
objects linked to by certain roles. Currently only the ``:ref:`` and ``:doc:`` roles are
supported.

.. figure:: ../../resources/images/definition-demo.gif
   :align: center
