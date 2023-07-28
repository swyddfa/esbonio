``lsp-mode`` requires that the server be registered so that is knows how and
when to start the server.

.. literalinclude:: ./emacs-lsp-mode/lsp-mode-minimal.el
   :language: elisp
   :start-after: ;; Register the Esbonio language server with lsp-mode
   :end-before: ;; Setup some keybindings
