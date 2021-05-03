Emacs
=====

.. note::

   While I like to play around now and again with Emacs, I'm hardly an expert! If you
   know of a better way to set this up, feel free to open a pull request!

There are multiple LSP clients available in the Emacs ecosystem.

- `eglot`_ a more minimal Language Client that integrates tightly with features built
  into Emacs such as ``project.el``, ``xref.el`` and ``eldoc.el``.
- `lsp-mode`_ the Language Client with all the bells and whistles, integrates into the
  wider Emacs ecosystem with packages like ``projectile``, ``treemacs`` and ``ivy``.

This page contains a number of sample configurations that you can use to get started.

Eglot -- Minimal Config
-----------------------

.. figure:: /_static/images/emacs-eglot-minimal.png
   :align: center
   :width: 80%

   Using Esbonio with Emacs and the ``eglot-minimal.el`` configuration.

This barebones configuration should be just enough to get things up and running with
Emacs, Esbonio and Eglot, might be useful to help track down configuration issues.

The key to setting up ``eglot`` is to tell it about the language server, how to start
it and that we want to use it with ``*.rst`` files

.. literalinclude:: /_static/sample-configs/emacs/eglot-minimal.el
   :language: elisp
   :start-after: ;; files.
   :end-before: ;; Setup some keybindings


To try this config on your machine.

1. Make sure you've followed the :ref:`editor_integration_common`.
2. Download :download:`eglot-minimal.el </_static/sample-configs/emacs/eglot-minimal.el>`
   to a folder of your choosing.
3. Edit ``eglot-minimal.el`` to set the path to the Python executable be the one in the
   virtual environment you just installed the language server into.
4. Run the following command to launch a separate instance of Emacs isolated from your
   usual configuraiton::

     emacs -Q -l eglot-minimal.el

Eglot -- Extended Config
------------------------

Here is a configuration with a few more bells and whistles that aims to showcase what can be
achieved with some additional configuration.


LSP Mode -- Minimal Config
--------------------------

LSP Mode -- Extended Config
---------------------------


.. _eglot: https://github.com/joaotavora/eglot
.. _lsp-mode: https://emacs-lsp.github.io/lsp-mode/
