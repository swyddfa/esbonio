Your First Extension
--------------------

This tutorial should cover everything you need to know to create your first extension.
It assumes that you're familiar with using the standard language server from your editor of choice.

It is also recommended that you read through the section on the server's :ref:`lsp_architecture`.

Final Result
^^^^^^^^^^^^

Setup
^^^^^

Let's first create a new sphinx project using ``sphinx-quickstart``, for our purposes it doesn't really matter what options you choose here.

.. code-block:: console

   $ sphinx-quickstart
   Welcome to the Sphinx 4.4.0 quickstart utility.

   Selected root path: .

   > Separate source and build directories (y/n) [n]: n
   > Project name: Extension Basics
   > Author name(s): .
   > Project release []:
   > Project language [en]:

   Creating file ...

   Finished: An initial directory structure has been created.

   You should now populate your master file /home/.../index.rst and create other documentation
   source files. Use the Makefile to build the docs, like so:
      make builder
   where "builder" is one of the supported builders, e.g. html, latex or linkcheck.

In the project's ``conf.py`` we'll enable the :doc:`sphinx.ext.extlinks <sphinx:usage/extensions/extlinks>` extension which, with a little bit of configuration, handle the creation of the custom role for us.

.. literalinclude:: ../../../lib/esbonio/tests/extension-basics/workspace/conf.py
   :language: python
   :start-after: # fmt: off
   :end-before: # fmt: on

If you were to use the default language server with this project, you should find that language server can automatically detect the new ``:repo:`` role and include it in its completion suggestions.

.. figure:: /images/ext-basics/default.gif
   :align: center

   Default language server behaviour

However, the language server cannot automatically determine any other information about this role but it does provide mechanisms for us to provide the information ourselves.
Let's start by providing some documentation on how the ``:repo:`` role can be used.

Providing Documentation
^^^^^^^^^^^^^^^^^^^^^^^

The easiest way to extend the language server is to add an ``esbonio_setup`` function directly to the project's ``conf.py``.
This function will be called with the language server instance during startup and allow you to extend it to your liking.

We'll start by trying to access the :class:`~esbonio.lsp.roles.Roles` language feature

.. literalinclude:: ../../../lib/esbonio/tests/extension-basics/workspace/conf.py
   :language: python
   :start-at: def esbonio_setup
   :end-before: documentation

Assuming that is successful, we can go ahead and register the documentation using the role feature's :meth:`~esbonio.lsp.roles.Roles.add_documentation` method.

.. literalinclude:: ../../../lib/esbonio/tests/extension-basics/workspace/conf.py
   :language: python
   :start-at: roles.add_documentation

The most challenging part of providing documentation for a role (and directives) is providing the correct key for the documentation.
It takes the form of ``name(dotted.implementation.name)`` where the ``name`` is what the user types into a reStructured text document - ``repo`` in this case.

Since role and directive names can be overridden with alternate implementations it's necessary to provide the full ``dotted.implementation.name`` of the implementation you wish to document.

.. tip::

   If you are not sure what the implementation's name would be (such as when the role is implemented for you by the ``sphinx.ext.extlinks`` extension!) you can always check the ``CompletionItem`` record that is returned by the language server.

   .. figure:: /images/ext-basics/impl-name.png
      :align: center
