
Development Environments
========================

.. _devenv_lsp:

Language Server
---------------

Assuming that you already have `Python`_ available you can create a virtual
environment in the root of the repository with the following command::

   $ python -m venv .env

Then to install all the tools and dependencies required to work on the Language
Server, you need to activate your newly created environment and run the
following commands::

   $ source .env/bin/activate
   $ cd lib/esbonio
   $ pip install -e .[dev]

.. _Python: https://www.python.org/

VSCode
------

As the VSCode extension relies on the Language Server for much of its
functionality the first step in setting up your development environment would be
to follow the setup guide for the :ref:`devenv_lsp`.

Assuming that you have the language server up and running you will next need
to ensure you have `VSCode`_ and `npm`_ available on your system.

Next open a terminal in the ``code/`` directory of the repository and run the
following::

   $ npm install

This will download all the dependencies required to work on the extension. Once
completed open the root of the repository in VSCode and hit :kbd:`F5`, this will
build and open the extension in a separate instance that can be debugged from
the main instance.



.. _VSCode: https://code.visualstudio.com/
.. _npm: https://www.npmjs.com/get-npm
