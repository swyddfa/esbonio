How To Setup the Development Environment
========================================

.. highlight:: none

.. warning::

   This guide assumes you are **not** using Windows.
   If you are using Windows, you may still be able to get some use from it, but feel free to `open an issue <https://github.com/swyddfa/esbonio/issues/new>`__ if you get stuck!

This guide outlines how to setup the development environment(s) necessary to work on the various components located in the `swyddfa/esbonio <https://github.com/swyddfa/esbonio>`__ GitHub repository.

**Dev Container**

This repository provides a simple `devcontainer <https://containers.dev/overview>`__ definition that you can use.

Note that using this container is **entirely optional** and you can easily setup a development environment without it.
The devcontainer is only used to provide a known starting point from which all scripts and automations in the repository can build against.

.. dropdown:: .devcontainer/devcontainer.json

   .. literalinclude:: ../../../.devcontainer/devcontainer.json
      :language: json


**Makefiles**

.. _uv: https://docs.astral.sh/uv/
.. _Makefiles: https://makefiletutorial.com/

*Use of the Makefiles is optional, but recommended to those who are unfamiliar with the repository.*

Many common tasks, from installing tools such as `uv`_ to packaging the VSCode extension have been automated in `Makefiles`_ located throughout the repository.

While they are written and tested with the environment provided by the devcontainer in mind, the Makefiles try, where possible, to work in "any" Unix-like environment.
This is done by reusing tools already present on your ``$PATH`` and automatically installing any missing tools into ``$HOME/.local``.

Running ``make tools`` in the root of the repository will list all tools required for this project, **automatically installing them if necessary** ::

   $ make tools
   ...
   /home/vscode/.local/bin/uv      uv 0.5.21
   /home/vscode/.local/bin/python  Python 3.13.1
   /home/vscode/.local/bin/hatch   Hatch, version 1.14.0
   /home/vscode/.local/bin/pre-commit      pre-commit 4.0.1
   /home/vscode/.local/bin/npm     10.8.2
   /home/vscode/.local/bin/npx     10.8.2

.. tip::

   The provided devcontainer is the result of taking a standard Ubuntu image and running ``make tools``

Full details on how the tools are installed can be found in the ``.devcontainer/tools.mk`` file

.. dropdown:: .devcontainer/tools.mk

   .. literalinclude:: ../../../.devcontainer/tools.mk
      :language: make


.. _devenv_lsp:

Language Server
---------------

The language server is written in pure Python, so if you are familiar with Python development, you should not find anything too surprising here.

We use `hatch <https://hatch.pypa.io/latest/>`__ both for packaging the language server as well as managing all the test environments.

To produce both source and wheel packages run the following command from the ``lib/esbonio`` directory ::

   $ hatch build
   ───────────────────────────────────────── sdist ─────────────────────────────────────────
   dist/esbonio-1.0.0b9.tar.gz
   ───────────────────────────────────────── wheel ─────────────────────────────────────────
   dist/esbonio-1.0.0b9-py3-none-any.whl

Running tests is a little more involved, while running ``hatch test`` indeed looks promising ::

   $ hatch test
   ========================================= test session starts =========================================
   platform linux -- Python 3.13.1, pytest-8.3.4, pluggy-1.5.0
   rootdir: /workspaces/develop/lib/esbonio
   configfile: pyproject.toml
   plugins: asyncio-0.25.2, rerunfailures-14.0, mock-3.14.0, lsp-1.0.0b2, xdist-3.6.1
   asyncio: mode=Mode.AUTO, asyncio_default_fixture_loop_scope=function
   collected 254 items

   tests/server/feature/test_completion.py ...................                                     [  7%]
   tests/server/features/test_directive_completion.py ...............................              [ 19%]
   tests/server/features/test_logging.py .......                                                   [ 22%]
   tests/server/features/test_role_completion.py ...........                                       [ 26%]
   tests/server/features/test_sphinx_config.py ....s..s......ss.s.ss                               [ 35%]
   tests/server/test_configuration.py .....s.s.s.s.s.s.s.s.s.s......ssssss......                   [ 51%]
   tests/server/test_patterns.py ................................................................. [ 77%]
   ..........................................................                                      [100%]

   =================================== 231 passed, 23 skipped in 1.24s ===================================

This is in fact only a small subset of the full test suite!
To see the full set of test environments, run the following command ::

   $ hatch env show --internal
                                                                Matrices
   ┏━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
   ┃ Name       ┃ Type    ┃ Envs                      ┃ Dependencies                    ┃ Environment variables ┃ Scripts     ┃
   ┡━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
   │ hatch-test │ virtual │ hatch-test.py3.9          │ coverage-enable-subprocess==1.0 │ UV_PRERELEASE=allow   │ cov-combine │
   │            │         │ hatch-test.py3.10         │ coverage[toml]~=7.4             │                       │ cov-report  │
   │            │         │ hatch-test.py3.11         │ pytest-lsp>=1.0b0               │                       │ run         │
   │            │         │ hatch-test.py3.12         │ pytest-mock~=3.12               │                       │ run-cov     │
   │            │         │ hatch-test.py3.13         │ pytest-randomly~=3.15           │                       │             │
   │            │         │ hatch-test.py3.9-sphinx6  │ pytest-rerunfailures~=14.0      │                       │             │
   │            │         │ hatch-test.py3.9-sphinx7  │ pytest-xdist[psutil]~=3.5       │                       │             │
   │            │         │ hatch-test.py3.10-sphinx6 │ pytest~=8.1                     │                       │             │
   │            │         │ hatch-test.py3.10-sphinx7 │                                 │                       │             │
   │            │         │ hatch-test.py3.11-sphinx6 │                                 │                       │             │
   │            │         │ hatch-test.py3.11-sphinx7 │                                 │                       │             │
   │            │         │ hatch-test.py3.12-sphinx6 │                                 │                       │             │
   │            │         │ hatch-test.py3.12-sphinx7 │                                 │                       │             │
   │            │         │ hatch-test.py3.13-sphinx6 │                                 │                       │             │
   │            │         │ hatch-test.py3.13-sphinx7 │                                 │                       │             │
   │            │         │ hatch-test.py3.10-sphinx8 │                                 │                       │             │
   │            │         │ hatch-test.py3.11-sphinx8 │                                 │                       │             │
   │            │         │ hatch-test.py3.12-sphinx8 │                                 │                       │             │
   │            │         │ hatch-test.py3.13-sphinx8 │                                 │                       │             │
   └────────────┴─────────┴───────────────────────────┴─────────────────────────────────┴───────────────────────┴─────────────┘

In addition to an environment for each version of Python we support, we also define an environment for each version of Sphinx we support.
The following will run all the tests for a given Python version ::

   $ hatch test --include py=3.x

See the `upstream documentation <https://hatch.pypa.io/latest/tutorials/testing/overview/>`__ for more details on the ``hatch test`` command.

Makefile Targets
^^^^^^^^^^^^^^^^

For convenience the following make targets are available in the ``lib/esbonio`` directory

- ``make dist``: Package esbonio as a ``*.whl`` file
- ``make test``: Run the full test suite for your current Python version


.. _Python: https://www.python.org/

VSCode Extension
----------------

The development environment for the VSCode is quite involved as not only does it depend on the language server and the TypeScript glue code, but it also requires two separate, standalone Python environments.
The fully packaged version of the extension contains the following key folders ::

   esbonio-0.96.1.vsix
   └─ extension/
      ├─ bundled/
      │  ├─ env/ (3330 files) [50.93 MB]  <-- Bundled fallback Sphinx environment
      │  └─ libs/ (530 files) [4.39 MB]   <-- Bundled language server and dependencies
      ├─ dist/
      │  └─ node/ (1 file) [794.54 KB]    <-- Glue compiled JavaScript code that integrates the server into VSCode
      ├─ guides/
      └─ syntaxes/

All of which have to be setup on your machine

.. tip::

   When working on the VSCode extension, the provided :ref:`Makefile <devenv-vscode-makefile>` is especially useful.

**Compiled TypeScript**

To compile the necessary type script code, first you need to install the necessary dependencies.
Run the following command in the ``code/`` directory ::

   $ npm ci

Then to compile ::

   $ npm run compile

Alternatively, if you want to automatically re-compile each time you modify the source ::

   $ npm run watch

**Python Environments**

To setup the necessary Python environments, run the following commands in the ``code/`` directory ::

   $ python -m pip install -t ./bundled/env --no-cache-dir --implementation py --no-deps --upgrade -r ./requirements-env.txt
   $ python -m pip install -t ./bundled/libs --no-cache-dir --implementation py --no-deps --upgrade -r ./requirements-libs.txt

**Install Esbonio**

The previous ``pip install`` commands installed the necessary third-party dependencies however, we still need to install the ``esbonio`` server itself.
Chances are you will want to use the version that is in the repository, in which case all we have to do is create a symlink to the right folder.
Run the following command in the ``code/`` folder, replacing ``/path/to/repo`` with the actual path to your clone of the repository. ::

   $ ln -s /path/to/repo/lib/esbonio/esbonio bundled/libs/esbonio

With that complete you should have everything you need to run the ``VSCode Extension`` launch configuration in VSCode!

**Install Workspace Extension (Optional)**

If you are working on just the language server itself, you can install the VSCode Extension as a `workspace local extension`_, which removes the need for a separate debug VSCode instance.
To do this, create a symlink from the ``.vscode/extensions`` directory to the ``code/`` directory ::

   $ ln -s /path/to/repo/.vscode/extensions/esbonio /path/to/repo/code

You should then see the option to install the extension in the :guilabel:`Recommended` section of the VSCode extensions pane.

.. admonition:: Call for testing!

   You may have noticed we have not mentioned any automated tests... that's because there isn't any! 😱

   After many attempts, I never figured out a way to write tests that I felt were useful enough to be worth the effort.
   If you know how to write tests for a VSCode extension I'd love to hear it!

.. _devenv-vscode-makefile:

Makefile Targets
^^^^^^^^^^^^^^^^

The ``Makefile`` in the ``code/`` directory provides the following high-level targets

``make clean``
   Remove all non-source files (``bundlded/``, ``node_modules``, etc.)

``make compile``
   - Install all required development dependencies
   - Bootstrap required Python environments (``bundled/libs``, ``bundlded/env``)
   - Create a symlink to ``lib/esbonio``, so that the extension uses the in-repo version of the ``esbonio`` server
   - Compile the TypeScript under ``code/src/`` into JavaScript under ``dist/``

``make watch``
   Same as ``make compile``, but automatically recompile TypeScript code when modified.

``make install``
   Same as ``make compile``, but also create a symlink from ``.vscode/extensions/esbonio`` to ``code/``, allowing you to install the in-repo version of the extension as a `workspace local extension`_

``make dist``
   - Install all required development dependencies
   - Bootstrap required Python environments (``bundled/libs``, ``bundlded/env``)
   - Install esbonio from a ``*.whl`` file into ``bundled/libs``.
     By default, the ``*.whl`` file will be the latest release downloaded from PyPi.
     This however, can be changed by setting the ``WHL`` variable when invoking make ::

      $ WHL=./esbonio-1.0-py3-none-any.whl make dist

   - Compile the TypeScript under ``code/src/`` into JavaScript under ``dist/``


.. _VSCode: https://code.visualstudio.com/
.. _npm: https://www.npmjs.com/get-npm
.. _workspace local extension: https://code.visualstudio.com/updates/v1_89#_local-workspace-extensions
