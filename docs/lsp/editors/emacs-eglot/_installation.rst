Configuring ``eglot`` can be as straightforward as updating the ``eglot-server-programs`` list
to register the language server and how to start it, and running ``eglot-ensure`` whenever we
open an ``*.rst`` file.

.. literalinclude:: emacs-eglot/eglot-minimal.el
   :language: elisp
   :start-at: (require 'eglot)
   :end-at: (add-hook 'rst-mode-hook
