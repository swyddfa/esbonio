Contributing
============

Development Environment
-----------------------

As the VSCode extension relies on the Language Server for much of its
functionality the first step in setting up your development environment would be
to follow the setup guide for the :ref:`Language Server <lsp_devenv>`.

Assuming that you have the language server up and running you will next need
to ensure you have `VSCode`_ and `npm`_ available on your system.

Next open a terminal in the ``code/`` directory of the repository and run the
following::

   npm install

This will download all the dependencies required to work on the extension. Once
completed open the root of the repository in VSCode and hit :kbd:`F5`, this will
build and open the extension in a separate instance that can be debugged from
the main instance.



.. _VSCode: https://code.visualstudio.com/
.. _npm: https://www.npmjs.com/get-npm