How To Use Esbonio With...
==========================

There are (almost!) as many ways to manage a Python environment as there are packages on PyPi!
This guide outlines how to configure ``esbonio`` to use the right environment for your project.

... Hatch
---------

If for example, you used `hatch <https://hatch.pypa.io/latest/>`__ to define an environment in which you build your documentation

.. code-block:: toml

   [tool.hatch.envs.docs]
   dependencies = [
      "sphinx",
      "sphinx-design",
      "furo",
      "myst-parser",
   ]
   scripts.build = "sphinx-build -M dirhtml . ./_build"

Then you should set :esbonio:conf:`esbonio.sphinx.pythonCommand` to

.. code-block:: toml

   [tool.esbonio.sphinx]
   pythonCommand = ["hatch", "-e", "docs", "run", "python"]

... Poetry
----------

Given a set of dependencies managed through `Poetry <https://python-poetry.org/>`__

.. code-block:: toml

   [tool.poetry.dependencies]
   python = ">=3.9"
   cattrs = ">=23.1.2"
   lsprotocol = "2024.0.0a2"
   websockets = { version = ">=11.0.3", optional = true }

   [tool.poetry.group.docs.dependencies]
   myst-parser = ">=2.0"
   sphinx = ">=7.1.2"
   sphinx-design = ">=0.5.0"
   sphinx-rtd-theme = ">=1.3.0"

You will first need to make sure that ``poetry`` has created the environment with the required dependencies

.. code-block:: console

   $ poetry install --with docs

Then you should set :esbonio:conf:`esbonio.sphinx.pythonCommand` to

.. code-block:: toml

   [tool.esbonio.sphinx]
   pythonCommand = ["poetry", "run", "python"]

... venv / virtualenv
---------------------

.. tip::

   Virtual environments are not portable between machines or even Python versions, which means the best place to set the :esbonio:conf:`esbonio.sphinx.pythonCommand` option is in your language client, rather than your project's ``pyproject.toml``.

Assuming you already have an envrionment that you use to build your documentation

.. code-block:: console

   (venv) $ python -m pip list
   Package                       Version    Editable project location
   ----------------------------- ---------- -------------------------------------------------
   ...
   Sphinx                        7.1.2
   sphinx_design                 0.5.0
   sphinx-rtd-theme              2.0.0
   sphinxcontrib-applehelp       1.0.4
   sphinxcontrib-devhelp         1.0.2
   sphinxcontrib-htmlhelp        2.0.1
   sphinxcontrib-jquery          4.1
   sphinxcontrib-jsmath          1.0.1
   sphinxcontrib-qthelp          1.0.3
   sphinxcontrib-serializinghtml 1.1.5
   urllib3                       2.1.0

Then you set :esbonio:conf:`esbonio.sphinx.pythonCommand` to the full path to the ``python`` executable contained in the environment (which will be slightly different depending on your operating system)

.. tab-set::

   .. tab-item:: Linux / macOS

      .. code-block:: toml

         [tool.esbonio.sphinx]
         pythonCommand = ["/home/user/Projects/myproject/venv/bin/python"]

   .. tab-item:: Windows

      .. code-block:: toml

         [tool.esbonio.sphinx]
         pythonCommand = ["C:\\Users\\user\\Projects\\myproject\\Scripts\\python.exe"]
