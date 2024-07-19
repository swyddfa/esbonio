Editor Integration
------------------

.. toctree::
   :hidden:

   Emacs <howto/emacs>
   Kate <howto/kate>
   Neovim <howto/nvim>

While the :doc:`tutorial </lsp/getting-started>` focuses on using ``esbonio`` from within VSCode.
These guides will help you get ``esbonio`` setup with your editor of choice

.. admonition:: Don't see your favourite editor?

   Feel free to submit a pull request with steps on how to get started or if you're not
   sure on where to start, `open an issue`_ and we'll help you figure it out.

.. _open an issue: https://github.com/swyddfa/esbonio/issues/new

.. grid:: 2 2 3 4
   :gutter: 1

   .. grid-item-card:: Emacs
      :link: integrate-emacs
      :link-type: ref
      :text-align: center

      How to use esbonio within Emacs, using either ``eglot`` or ``lsp-mode`` as your language client.

   .. grid-item-card:: Neovim
      :link: integrate-nvim
      :link-type: ref
      :text-align: center

      Using ``esbonio`` with Neovim's built in language client.

Additional Features
===================

The language server provides additional notifications and commands that are not part of the LSP specification.
This means that they require additional client side integration code to be enabled.

Theses features are not a requirement to use ``esbonio``, but they do offer some quality of life improvements.

.. toctree::
   :maxdepth: 1

   Sphinx Processes <reference/sphinx-processes>
   Previews <reference/previews>
