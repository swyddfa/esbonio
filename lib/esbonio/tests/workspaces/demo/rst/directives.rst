Directives
==========

This page provides an overview of the features Esbonio provides to make working with reStructuredText :external:std:ref:`rst-directives` easier.

Completion
----------

The most obvious feature is the completion suggestions, try inserting a ``.. note::`` directive on the next line

.. Add your note here...

In addition to directive names, Esbonio supports suggesting values many kinds of arguments given to a directive, including.

**Filepaths**

Completing local filepaths is supported for

- `figure <https://docutils.sourceforge.io/docs/ref/rst/directives.html#figure>`__
- `image <https://docutils.sourceforge.io/docs/ref/rst/directives.html#image>`__
- `include <https://docutils.sourceforge.io/docs/ref/rst/directives.html#image>`__
- :external+sphinx:rst:dir:`literalinclude`

.. Try using the `literalinclude` directive to insert the contents of this project's conf.py here...

**Pygments Lexers**

Sphinx uses the `pygments <https://pygments.org/>`__ library for its syntax highlighting.
Esbonio can offer the names of available lexers as suggestions for the following directives.

- :external+sphinx:rst:dir:`code`
- :external+sphinx:rst:dir:`code-block`
- :external+sphinx:rst:dir:`highlight`
- :external+sphinx:rst:dir:`sourcecode`

.. Try inserting a code block on the next line...

Document Links
--------------

Many text editors will automatically detect links to webpages e.g. https://sphinx-doc.org and make them clickable.
The `textDocument/documentLink <https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentLink>`__ request allows language servers to do the same.

When it makes sense to, ``esbonio`` will add clickable links to many directive arguments, including

- Local files

  .. code-block:: rst

     .. include:: ./directives.rst

GoTo ...
--------

... Definition
^^^^^^^^^^^^^^

Esbonio supports GoTo Definition requests for directive arguments, including

- Local files

  .. code-block:: rst

     .. include:: ./symbols.rst
