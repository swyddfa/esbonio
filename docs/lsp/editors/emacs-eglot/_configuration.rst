However, you will likely likely want to set some of the language server's configuration
options which are passed as ``initialization-options`` during startup. They are set
by subclassing ``eglot-lsp-server`` and implementing the ``eglot-initialization-options``
method to return them.

.. literalinclude:: ./editors/emacs-eglot/eglot-extended.el
   :dedent: 2
   :language: elisp
   :start-at: (defclass eglot-esbonio (eglot-lsp-server) ()
   :end-before: (add-to-list 'eglot-server-programs

Then when it comes to adding the entry to ``eglot-server-programs`` the ``eglot-esbonio``
class needs to be prepended to the list specifying the server start command.

.. literalinclude:: ./editors/emacs-eglot/eglot-extended.el
   :dedent: 2
   :language: elisp
   :start-at: (add-to-list 'eglot-server-programs
   :end-before: (use-package rst

The following is a list of all the available options
