.. _integrate-emacs:

How To Integrate Esbonio with Emacs
===================================

This guide covers how to setup ``esbonio`` with Emacs using the two main language client implementations:

- `eglot <https://github.com/joaotavora/eglot>`__ a mimialistic implementation, relies on built-in functionality where possible. Built into Emacs since v29.1

- `lsp-mode <https://emacs-lsp.github.io/lsp-mode/>`__ integrates well with third party packages like treemacs and helm.

Installation
------------

.. highlight:: none

.. include:: /_includes/installation.rst

The `esbonio.el <https://github.com/swyddfa/esbonio.el>`__ package provides the necessary "glue code" to integrate ``esbonio`` with both the ``eglot`` and ``lsp-mode`` clients.

.. tab-set::

   .. tab-item:: eglot
      :sync: eglot

      .. code-block:: elisp

         (use-package esbonio
           :vc (esbonio :url "https://github.com/swyddfa/esbonio.el" :rev "main")
           :hook ((rst-mode . esbonio-eglot-ensure)))

   .. tab-item:: lsp-mode
      :sync: lsp-mode

      .. code-block:: elisp

         (use-package esbonio
           :vc (esbonio :url "https://github.com/swyddfa/esbonio.el" :rev "main")
           :hook ((rst-mode . esbonio-lsp-deferred)))  ;; or `esbonio-lsp'

Configuration
-------------

It's recommended to store as many project-specific options as possible in your ``pyproject.toml`` file

.. code-block:: toml

   [tool.esbonio.sphinx]
   buildCommand = ["sphinx-build", "-M", "html", "docs", "docs/_build"]
   pythonCommand = ["uv", "run", "python"]

.. tip::

   See :ref:`lsp-configure-sphinx-build-env` and :ref:`lsp-configure-sphinx-build-cmd` guides for more examples of these settings.

However for options that are only applicable to your setup (e.g. logging), configuration options  can also be set through Emacs itself.

.. tab-set::

   .. tab-item:: eglot
      :sync: eglot

      Settings can be provided through setting ``eglot-workspace-configuration`` in a ``.dir-locals.el`` file in the root of your workspace.

      .. code-block:: elisp

         ((rst-mode
           . ((eglot-workspace-configuration
               . ((esbonio
                  . ((logging
                      . ((level . "debug"))))))))))


   .. tab-item:: lsp-mode
      :sync: lsp-mode

      Setting can be provided through evaluating the ``lsp-register-custom-settings`` function in a ``.dir-locals.el`` file in the root of your workspace.

      .. code-block:: elisp

         ((rst-mode
           . ((eval . (lsp-register-custom-settings
                       '(("esbonio.logging.level" "debug")
                         ("esbonio.logging.stderr" nil t)  ; Boolean values require the extra `t` indicating that they are booleans.
                         ("esbonio.logging.filepath" "esbonio.log")))))))

.. seealso::

   :ref:`lsp-configuration`
      For details on all available configuration options
