Relevent To
===========

The ``esbonio.relevant_to`` extension is similar to the `sphinx-panels`_ and `sphinx-tabs`_ extensions, where you can define sections of documentation that is only relevant to a given subject (e.g. Python version) and be able to choose between them.

However, instead of presenting these sections as tabs, this extension uses a dropdown which scales better when you have a large collection of subjects to cover (like text editors!)

Additionally this extension

- Reflects the chosen topic in the page's URL, making subject choices linkable
- Uses `htmx`_ to swap out the relevant sections.

See the Esbonio language server's :ref:`lsp_getting_started` guide for an example of this extension in action.

.. note::

   This extension currently only supports HTML builders.

.. _htmx: https://htmx.org/
.. _sphinx-panels: https://sphinx-panels.readthedocs.io/en/latest/index.html#tabbed-content
.. _sphinx-tabs: https://sphinx-tabs.readthedocs.io/en/latest/


Getting Started
---------------

The ``esbonio.relevant_to`` is available through the ``esbonio-extensions`` Python package.

.. code-block:: console

   $ pip install esbonio-extensions

Ensure that the extension is enabled by including ``esbonio.relevant_to`` in the ``extensions`` list inside your project's ``conf.py``::

   extensions = [
      "esbonio.relevant_to"
   ]


Then within your documentation, "relevant sections" are defined using the :rst:dir:`relevent-to` directive.

.. rst:directive:: relevent-to

   Define sections that can be swapped out based on the chosen subject.
   Consider the following example.

   .. code-block:: rst

      .. relevant-to:: Colour

         Blue
            The chosen colour is blue.

         Green
            The chosen colour is green.

         Red
            The chosen colour is red.

   The argument to the directive defines the category of subject this section is about. The content of the directive must be a valid `definition list <https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#definition-lists>`_ where the term is the name of the subject (``Red``, ``Green`` or ``Blue`` in this case) and the definition is the term's corresponding content.

   Here is how the above example is rendered.

   .. relevant-to:: Colour

      Blue
         The chosen colour is blue.

      Green
         The chosen colour is green.

      Red
         The chosen colour is red.

   The body of a definition can contain most reStructuredText constructs including roles and directives

   .. literalinclude:: /lsp/getting-started.rst
      :language: rst
      :start-at: .. relevant-to:: Editor
      :end-before: Emacs

   However section titles are not supported.
