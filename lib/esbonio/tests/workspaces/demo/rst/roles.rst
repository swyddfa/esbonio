Roles
=====

This page provides an overview of the features Esbonio provides to make working with reStructuredText :external:std:ref:`rst-roles` easier.

.. _rst-roles-completion:

Completion
----------

The most obvious feature is the completion suggestions, try inserting a ``:ref:`` role on the next line that links to the ``rst-roles-completion`` label defined above.

.. Add your reference here...

In addition to ``:ref:`` labels, ``esbonio`` supports suggesting values for manny other types of target

- Local docnames for the :external:rst:role:`doc` role
- Local filenames for the :external:rst:role:`download` role
- Python objects for roles like :external:rst:role:`py:class`, :external:rst:role:`py:func` and more!
- Targets defined in *other* Sphinx documentation sites for the :external:rst:role:`external` role!
  See :external:std:ref:`ext-intersphinx` for more details

Feel free to experiment with each of the roles mentioned above!

Document Links
--------------

Many text editors will automatically detect links to webpages e.g. https://sphinx-doc.org and make them clickable.
The `textDocument/documentLink <https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentLink>`__ request allows language servers to do the same.

When it makes sense to, ``esbonio`` will add clickable links to many role targets, including

- :doc:`Local docname references </myst/roles>`
- Local files :download:`./roles.rst`
- Intersphinx references e.g. :external:std:ref:`logging-exceptions`

See for yourself by :kbd:`Ctrl`\ +Clicking one of the above references

GoTo ...
--------

... Definition
^^^^^^^^^^^^^^

Esbonio supports GoTo Definition requests for role targets, including

- Local files :download:`./roles.rst`
- Documents :doc:`/myst/roles`
- References :ref:`myst-roles-completion`
- Python objects :py:class:`counters.pattern.PatternCounter`

Try invoking GoTo Definition on any of the above targets

Hover
-----

Esbonio provides documentation hovers for role targets, including

- Local Python objects, for example

  - :py:class:`counters.pattern.PatternCounter`
  - :meth:`counters.pattern.PatternCounter.fromstr`
  - :obj:`counters.pattern.DEFAULT_PATTERN`

Hover over any of the above targets to see their associated content
