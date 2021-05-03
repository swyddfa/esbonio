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

.. Currently we only offer configs for "hand crafted" Emacs configs? Would it be worth
   offering configs that work within popular frameworks like Spacemacs and Doom - would
   there be any noticable difference in the config code we write?

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
3. Edit ``eglot-minimal.el`` to set the path to the Python executable to be the one in
   the virtual environment you just installed the language server into.
4. Run the following command to launch a separate instance of Emacs isolated from your
   usual configuraiton::

     emacs -Q -l eglot-minimal.el

Eglot -- Extended Config
------------------------

.. figure:: /_static/images/emacs-eglot-extended.png
   :align: center
   :width: 80%

   Using Esbonio and Emacs with the ``eglot-extended.el`` configuration

Here is a configuration with a few more bells and whistles that aims to showcase what
can be achieved with some additional configuration.

.. note::

   There seems to be a bug in this config where ``project.el`` is not being loaded
   correctly preventing ``eglot`` from starting. However, this only appears to be an
   issue on the first run so if you encounter this try restarting Emacs and it should
   magically fix itself.

This time the configuration makes use of `use-package`_ to install (if necessary) and
configure packages with a single declaration

.. literalinclude:: /_static/sample-configs/emacs/eglot-extended.el
   :language: elisp
   :start-after: ;; Most important, ensure the eglot is available and configured.
   :end-before: ;; UI Tweaks

To try this config on your machine

1. Make sure you've followed the :ref:`editor_integration_common`.
2. Download :download:`eglot-extended.el </_static/sample-configs/emacs/eglot-extended.el>`
   to a folder of your choosing.
3. Edit ``eglot-extended.el`` to set the path to the Python executable to be the one in
   the virtual environment you just installed the language server into.
4. Run the following command to launch a separate instance of Emacs isolated from your
   usual configuration::

     emacs -Q -l eglot-extended.el

LSP Mode -- Minimal Config
--------------------------

.. figure:: /_static/images/emacs-lsp-mode-minimal.png
   :align: center
   :width: 80%

   Using Esbonio and Emacs with the ``lsp-mode-minimal.el`` configuration

This should be just enough configuration to get Esbonio working with LSP Mode and Emacs,
might be useful when tracking down configuration issues.

Setting up LSP Mode is slightly more complicated than Eglot as there is more
infrastructure to navigate but it boils down to the same steps, tell LSP Mode how to
start the server and then tell it when it should be started.

.. literalinclude:: /_static/sample-configs/emacs/lsp-mode-minimal.el
   :language: elisp
   :start-after: ;; Register the Esbonio language server with lsp-mode
   :end-before: ;; Setup some keybindings

To try this config on your machine

1. Make sure that you've followed the :ref:`editor_integration_common`.
2. Download :download:`lsp-mode-minimal.el </_static/sample-configs/emacs/lsp-mode-minimal.el>`
   to a folder of your choosing.
3. Edit ``lsp-mode-minimal.el`` to set the path to the Python executable to be the one
   in the virtual environment you just installed the language server into.
4. Run the following command to launch a separate instance of Emacs isolated from your
   usual configuration::

     emacs -Q -l lsp-mode-minimal.el

LSP Mode -- Extended Config
---------------------------


.. _eglot: https://github.com/joaotavora/eglot
.. _lsp-mode: https://emacs-lsp.github.io/lsp-mode/
.. _use-package: https://github.com/jwiegley/use-package
