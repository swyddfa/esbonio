Glossary
========

Being a language server, it's inevitable that details of the `Language Server Protocol <https://microsoft.github.io/language-server-protocol/>`__ will leak into Esbonio's usage and documentation.

Below is a list of commonly used terms and their meaning.

.. glossary::
   :sorted:

   LSP
      `Language Server Protocol <https://microsoft.github.io/language-server-protocol/>`__

   URI
      Uniform Resource Identifier.

      URIs are used by the language server protocol to describe locations of local and remote files and folders, and even individual cells in a notebook document. e.g.

      - ``file:///home/path/to/file.txt``
      - ``vscode-vfs://github@develop/swyddfa/esbonio/README.md``
      - ``nb-cell-scheme://path/to/notebook.ipynb#cv32321``

   workspace
      Refers to project folder(s) that are currently open in the user's editor.

   workspace folder
      Some clients (like VSCode) support multiple project folders within a single application instance e.g.

      - ``/path/to/Apps/TextWriter``
      - ``/path/to/Libraries/libtext``

      The term *workspace folder* refers to a single project folder.
