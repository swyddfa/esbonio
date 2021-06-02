Emacs
=====

There are multiple LSP clients available in the Emacs ecosystem.

- `eglot`_ a more minimal Language Client that integrates tightly with features built
  into Emacs such as ``project.el``, ``xref.el`` and ``eldoc.el``.
- `lsp-mode`_ the Language Client with all the bells and whistles, integrates into the
  wider Emacs ecosystem with packages like ``projectile``, ``treemacs`` and ``ivy``.

This page contains a number of sample configurations that you can use to get started.

.. Currently we only offer configs for "hand crafted" Emacs configs? Would it be worth
   offering configs that work within popular frameworks like Spacemacs and Doom - would
   there be any noticable difference in the config code we write?

Eglot
-----

.. figure:: /images/emacs-eglot-extended.png
   :align: center
   :width: 80%

   Using Esbonio and Emacs with the ``eglot-extended.el`` configuration

Configuring ``eglot`` involves updating the ``eglot-server-programs`` list to tell it about
the language server and how to start it. As well as adding an ``rst-mode-hook`` that runs
``eglot`` in ``*.rst`` files.

.. literalinclude:: emacs/eglot-minimal.el
   :language: elisp
   :start-after: ;; files.
   :end-before: ;; Setup some keybindings

We provide a barebones configuration ``eglot-minimal.el`` that you can use either to experiment
with Eglot and Esbonio or as a basis for your own configuration. To try it out on your machine.

1. Make sure you've followed the :ref:`editor_integration_setup`.
2. Download :download:`eglot-minimal.el <emacs/eglot-minimal.el>`
   to a folder of your choosing.
3. Edit ``eglot-minimal.el`` to set the path to the Python executable to be the one in
   the virtual environment you just installed the language server into.
4. Run the following command to launch a separate instance of Emacs isolated from your
   usual configuration::

     emacs -Q -l eglot-minimal.el

Server Configuration
^^^^^^^^^^^^^^^^^^^^

The language server provides a number of :ref:`settings <editor_integration_config>` that
for example can be used to control the instance of Sphinx that the server manages.

To set these values via Eglot it's necessary to create a subclass of Eglot's
``eglot-lsp-server`` type and implement the ``eglot-initialization-options`` method to return
the settings you wish to set.

.. literalinclude:: emacs/eglot-extended.el
   :dedent: 2
   :language: elisp
   :start-at: (defclass eglot-esbonio (eglot-lsp-server) ()
   :end-before: (add-to-list 'eglot-server-programs

Then when it comes to adding the entry to ``eglot-server-programs`` the ``eglot-esbonio``
class needs to be prepended to the list specifying the server start command.

.. literalinclude:: emacs/eglot-extended.el
   :dedent: 2
   :language: elisp
   :start-at: (add-to-list 'eglot-server-programs
   :end-before: (use-package rst

We provide an extended configuration ``eglot-extended.el`` that sets a few of these settings
as well as including a few extras. Feel free to use it to experiment with Elgot and Esbonio
or use it as a starting point for your own configuration.

1. Make sure you've followed the :ref:`editor_integration_setup`.
2. Download :download:`eglot-extended.el <emacs/eglot-extended.el>`
   to a folder of your choosing.
3. Edit ``eglot-extended.el`` to set the path to the Python executable to be the one in
   the virtual environment you just installed the language server into.
4. Run the following command to launch a separate instance of Emacs isolated from your
   usual configuration::

     emacs -Q -l eglot-extended.el

.. note::

   There seems to be a bug in this config where ``project.el`` is not being loaded
   correctly preventing ``eglot`` from starting. However, this only appears to be an
   issue on the first run so if you encounter this try restarting Emacs and it should
   magically fix itself.

LSP Mode -- Minimal Config
--------------------------

.. figure:: /images/emacs-lsp-mode-minimal.png
   :align: center
   :width: 80%

   Using Esbonio and Emacs with the ``lsp-mode-minimal.el`` configuration

This should be just enough configuration to get Esbonio working with LSP Mode and Emacs,
might be useful when tracking down configuration issues.

Setting up LSP Mode is slightly more complicated than Eglot as there is more
infrastructure to navigate but it boils down to the same steps, tell LSP Mode how to
start the server and then tell it when it should be started.

.. literalinclude:: emacs/lsp-mode-minimal.el
   :language: elisp
   :start-after: ;; Register the Esbonio language server with lsp-mode
   :end-before: ;; Setup some keybindings

To try this config on your machine

1. Make sure that you've followed the :ref:`editor_integration_setup`.
2. Download :download:`lsp-mode-minimal.el <emacs/lsp-mode-minimal.el>`
   to a folder of your choosing.
3. Edit ``lsp-mode-minimal.el`` to set the path to the Python executable to be the one
   in the virtual environment you just installed the language server into.
4. Run the following command to launch a separate instance of Emacs isolated from your
   usual configuration::

     emacs -Q -l lsp-mode-minimal.el

LSP Mode -- Extended Config
---------------------------

.. figure:: /images/emacs-lsp-mode-extended.png
   :align: center
   :width: 80%

   Using Esbonio and Emacs with the ``lsp-mode-extended.el`` configuration.

Here is a configuration with a few more bells and whistles that aims to showcase what
can be achieved with some additional configuration.

.. literalinclude:: emacs/lsp-mode-extended.el
   :language: elisp
   :start-after: ;; Most important, ensure that lsp-mode is available and configured.
   :end-before: ;; UI Tweaks

This time the configuration makes use of `use-package`_ to install (if necessary) and
configure packages with a single declaration

To try this config on your machine

1. Make sure that you've followed the :ref:`editor_integration_setup`.
2. Download :download:`lsp-mode-extended.el <emacs/lsp-mode-extended.el>`
   to a folder of your choosing.
3. Edit ``lsp-mode-extended.el`` to set the path to the Python executable to be the one
   in the virtual environment you just installed the language server into.
4. Run the following command to launch a separate instance of Emacs isolated from your
   usual configuration::

     emacs -Q -l lsp-mode-extended.el

.. _eglot: https://github.com/joaotavora/eglot
.. _lsp-mode: https://emacs-lsp.github.io/lsp-mode/
.. _use-package: https://github.com/jwiegley/use-package
