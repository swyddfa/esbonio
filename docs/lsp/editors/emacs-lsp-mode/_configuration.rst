The language server can be configured by passing a number of ``initialization-options``
to it during startup. To set these values you need to pass a function to ``make-lsp-client``
that returns the options you wish to set.

.. literalinclude:: ./editors/emacs-lsp-mode/lsp-mode-extended.el
   :dedent: 3
   :language: elisp
   :start-at: (make-lsp-client
   :end-at: :server-id

The following is a list of all the available options.
