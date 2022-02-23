- ``eglot-minimal.el``: A barebones configuration, useful for debugging.
- ``eglot-extended.el``: A slightly more advanced configuration which demonstrates
  a few more features of the language server.

.. highlight:: console

To try one of these configurations out.

#. Download :download:`eglot-minimal.el <./editors/emacs-eglot/eglot-minimal.el>`
   or :download:`eglot-extended.el <./editors/emacs-eglot/eglot-extended.el>`
   to a folder of your choosing (not your ``.emacs.d/``).

#. Activate the virtual environment you installed the language server into::

      $ source .env/bin/activate

#. Run the following command to launch a separate instance of Emacs, isolated from your
   usual configuration::

      (.env) $ emacs -Q -l eglot-minimal.el  # or eglot-extended.el
