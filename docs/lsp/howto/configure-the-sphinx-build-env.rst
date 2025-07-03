.. _lsp-configure-sphinx-build-env:

How To Configure the Sphinx Build Environment
=============================================

Esbonio works by creating a background Sphinx process which it can use to build your documentation and extract information from it.
This of course, requires ``esbonio`` being able to execute this process within the correct Python environment.

Since there are many ways to define and manage Python environments, ``esbonio`` needs you to tell it how to run the ``python`` command so that it has access to the correct dependencies.
This is typically done by setting the :esbonio:conf:`esbonio.sphinx.pythonCommand` in your project's ``pyproject.toml`` file.

Below are some examples on how you would set this option depending on your choice of environment manager tool.

Hatch
-----

If you use `hatch <https://hatch.pypa.io/latest/>`__ to define the environment in which you build your documentation

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

Pipenv
------

If your project uses `Pipenv <https://pipenv.pypa.io/en/latest/index.html>`__ for its dependency management

.. code-block:: ini

   [[source]]
   url = "https://pypi.org/simple"
   verify_ssl = true
   name = "pypi"

   [packages]
   furo = "*"
   sphinx = "*"
   sphinx-design = "*"

Then :esbonio:conf:`esbonio.sphinx.pythonCommand` should be set to

.. code-block:: toml

   [tool.esbonio.sphinx]
   pythonCommand = ["pipenv", "run", "python"]

Poetry
------

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

venv / virtualenv
-----------------

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

Then set :esbonio:conf:`esbonio.sphinx.pythonCommand` to the full path to the ``python`` executable contained in the environment (which will be slightly different depending on your operating system)

.. tab-set::

   .. tab-item:: Linux / macOS

      .. code-block:: toml

         [tool.esbonio.sphinx]
         pythonCommand = ["/home/user/Projects/myproject/venv/bin/python"]

   .. tab-item:: Windows

      .. code-block:: toml

         [tool.esbonio.sphinx]
         pythonCommand = ["C:\\Users\\user\\Projects\\myproject\\venv\\Scripts\\python.exe"]

Alternatively, you can use the ``${venv:<path>}`` configuration variable, this allows you to provide just the path to the ``venv`` folder and ``esbonio`` will expand it to the correct path to the Python executable for your platform.
``<path>`` can either be an absolute path, or relative to the folder containing your ``pyproject.toml`` file.

For example, say your project had the following structure

.. code-block:: console

   $ tree myproject
   myproject
   ├── docs
   │   └── pyproject.toml
   └── venv

Then your ``pyproject.toml`` might look something like the following.

.. code-block:: toml

   [tool.esbonio.sphinx]
   pythonCommand = ["${venv:../venv}"]
