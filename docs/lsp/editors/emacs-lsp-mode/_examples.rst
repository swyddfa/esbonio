- ``lsp-mode-minimal.el``: A barebones configuration, useful for debugging.
- ``lsp-mode-extended.el``: A slightly more advanced configuration which demonstrates
  a few more features of the language server.

.. highlight:: console

To try one of these configurations out.

#. Download :download:`lsp-mode-minimal.el <./emacs-lsp-mode/lsp-mode-minimal.el>`
   or :download:`lsp-mode-extended.el <./emacs-lsp-mode/lsp-mode-extended.el>`
   to a folder of your choosing (not your ``.emacs.d/``).

#. Activate the virtual environment you installed the language server into::

      $ source .env/bin/activate

#. Run the following command to launch a separate instance of Emacs, isolated from your
   usual configuration::

      (.env) $ emacs -Q -l lsp-mode-minimal.el  # or lsp-mode-extended.el
