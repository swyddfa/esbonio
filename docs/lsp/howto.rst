.. _lsp-howto:

How To
======

This section contains a number of guides to help you get the most out of Esbonio.

.. toctree::
   :hidden:

   Migrate to v1 <howto/migrate-to-v1>

Editor Integration
------------------

.. toctree::
   :hidden:
   :maxdepth: 1

   Use Esbonio in Emacs <howto/use-esbonio-in-emacs>
   Use Esbonio in Neovim <howto/use-esbonio-in-nvim>

While the :doc:`tutorial </lsp/getting-started>` focuses on using ``esbonio`` from within VSCode.
These guides will help you get ``esbonio`` setup with your editor of choice

.. admonition:: Don't see your favourite editor?

   Feel free to submit a pull request with steps on how to get started or if you're not
   sure on where to start, `open an issue`_ and we'll help you figure it out.

.. _open an issue: https://github.com/swyddfa/esbonio/issues/new

.. grid:: 2 2 3 4
   :gutter: 1

   .. grid-item-card:: Emacs
      :link: howto/use-esbonio-in-emacs
      :link-type: doc
      :text-align: center

      How to use esbonio within Emacs, using either ``eglot`` or ``lsp-mode`` as your language client.

   .. grid-item-card:: Neovim
      :link: howto/use-esbonio-in-nvim
      :link-type: doc
      :text-align: center

      Using ``esbonio`` with Neovim's built in language client.
