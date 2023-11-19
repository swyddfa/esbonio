How To Use Esbonio in Emacs
===========================

There are two main language client implementations available in Emacs

- `eglot <https://github.com/joaotavora/eglot>`__ a mimialistic implementation, relies on built-in functionality where possible.
  Built into Emacs since v29.1

- `lsp-mode <https://emacs-lsp.github.io/lsp-mode/>`__ integrates well with third party packages like treemacs and helm.

Installation
------------

Install the language server using `pipx <https://pypa.github.io/pipx/>`__ ::

  $ pipx install esbonio


.. tab-set::

   .. tab-item:: eglot
      :sync: eglot

      Add esbonio to the ``eglot-server-programs`` list and enable ``eglot`` in ``rst-mode`` buffers

      .. code-block:: elisp

         (require 'eglot)
         (add-to-list 'eglot-server-programs '(rst-mode . ("esbonio")))
         (add-hook 'rst-mode-hook 'eglot-ensure)

Configuration
-------------

It's recommended to store as many project-specific options as possible in your ``pyproject.toml`` file

.. code-block:: toml

   [tool.esbonio.sphinx]
   buildCommand = [
     "sphinx-build", "-M", "html", "docs", "docs/_build"
   ]

.. tab-set::

   .. tab-item:: eglot
      :sync: eglot

      However, for options that are only applicable to your setup e.g. python environment these can be stored in a ``.dir-locals.el`` file in the root of your workspace.

      .. code-block:: elisp

         ((rst-mode
           . ((eglot-workspace-configuration
               . ((esbonio
                  . ((sphinx
                      . ((pythonCommand . ["/path/to/venv/bin/python"]))
                    ))
                 ))
             ))
         ))


.. seealso::

   :ref:`lsp-configuration`
      For details on all available configuration options



.. TODO:
.. Examples
.. --------
