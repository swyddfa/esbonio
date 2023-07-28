The language server can be installed using pip, or if you prefer, conda.

.. relevant-to:: Package Manager

   pip
      .. code-block:: console

         $ pip install esbonio

      If you want to try the latest developments before they are released you can use ``pip`` to install from the development branch.

      .. code-block:: console

         $ pip install "git+https://github.com/swyddfa/esbonio#egg=esbonio&subdirectory=lib/esbonio"

      For more information on this command see the documentation on pip's `VCS Support <https://pip.pypa.io/en/stable/topics/vcs-support/>`_.

   conda
      The language server is available through the ``esbonio`` package on `conda forge <https://anaconda.org/conda-forge/esbonio>`__.

      Installing ``esbonio`` from the ``conda-forge`` channel can be achieved by adding ``conda-forge`` to your channels with:

      .. code-block:: console

         $ conda config --add channels conda-forge
         $ conda config --set channel_priority strict

      Once the ``conda-forge`` channel has been enabled, ``esbonio`` can be installed with ``conda``

      .. code-block:: console

         $ conda install esbonio
