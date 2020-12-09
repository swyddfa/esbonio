Contributing
============

.. _lsp_devenv:

Development Environment
-----------------------

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