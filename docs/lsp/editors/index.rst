Editor Integrations
===================


.. toctree::
   :glob:
   :maxdepth: 1
   :hidden:

   *


This section contains notes on how to use the Language Server with various code editing
applications.


.. _editor_integration_setup:

Common Setup
------------

The language server works by creating an instance of Sphinx's application object and
inspecting it in order to provide completion suggestions etc.  In order for this
application instance to have the correct configuration, the language server needs to be
installed into and used from the same Python environment that you use when building your
documentation.

So the first step in integrating Esbonio with any editor is to ensure that the language
server has been installed into the correct environment. Unless you are using something
like the :ref:`editor_itegration_vscode` extension which attempts to automate this step for
you, this is something you'll have to do manually.

.. code-block:: console

   $ source .env/bin/activate
   (.env) $ pip install esbonio

Then you can refer to one of the following guides for specific details on using the
language server from your editor of choice.

.. hlist::
   :columns: 3

   - :doc:`/lsp/editors/emacs`
   - :doc:`/lsp/editors/vscode`

.. _editor_integration_config:

Common Configuration
--------------------

The following options are implemented directly by the language server and therefore
supported by any language client.

``esbonio.sphinx.confDir`` (string)
   The language server attempts to automatically find the folder which contains your
   project's ``conf.py``. If necessary this can be used to override the default discovery
   mechanism and force the server to use a folder of your choosing. Currently accepted
   values include:

   - ``/path/to/docs`` - An absolute path
   - ``${workspaceRoot}/docs`` - A path relative to the root of your workspace.

``esbonio.sphinx.srcDir`` (string)
   The language server assumes that your project's ``srcDir`` (the folder containing your
   rst files) is the same as your projects's ``confDir``. If this assumption is not true,
   you can use this setting to tell the server where to look. Currently accepted values
   include:

    - ``/path/to/src/`` - An absolute path
    - ``${workspaceRoot}/docs/src`` - A path relative to the root of your workspace
    - ``${confDir}/../src/`` - A path relative to your project's ``confDir``
