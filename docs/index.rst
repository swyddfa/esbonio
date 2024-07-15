Esbonio
=======

.. rubric:: esbonio -- (v.) to explain

Esbonio is a `Language Server`_ for `Sphinx`_ documentation projects.

Esbonio aids the writing process by resolving references, providing completion suggestions and highlighting errors.
It ensures your local build is always up to date, allowing you to preview your changes in (almost!) real-time.
The server itself can even be extended to better suit the needs of your project.

The primary goal of Esbonio is to reduce the friction that comes from trying to remember the specifics of a markup language, so that you can focus on your content and not your tooling.

.. grid:: 2
   :gutter: 2

   .. grid-item-card:: Getting Started
      :text-align: center
      :link: lsp-getting-started
      :link-type: ref

      Using Esbonio for the first time within VSCode.

   .. grid-item-card:: How-To Guides
      :text-align: center
      :link: lsp-howto
      :link-type: ref

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

      Documentation on extending the language server

.. toctree::
   :caption: Language Server
   :hidden:

   lsp/getting-started
   lsp/howto
   lsp/reference
   changelog

.. toctree::
   :caption: Extending
   :hidden:

   Getting Started <extending/getting-started>

.. toctree::
   :caption: Integrating
   :hidden:

   Getting Started <integrating/getting-started>

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
