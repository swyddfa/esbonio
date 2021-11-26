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
inspecting it in order to provide completion suggestions etc. In order for this
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
   - :doc:`/lsp/editors/kate`
   - :doc:`/lsp/editors/vscode`
   - :doc:`/lsp/editors/nvim`
   - :doc:`/lsp/editors/vim-coc`
   - :doc:`/lsp/editors/vim-lsp`

.. _editor_integration_config:

Initialization Options
----------------------

The following options are exposed as ``initializationOptions`` and should be
available in any language client.

``sphinx.confDir`` (string)
   The language server attempts to automatically find the folder which contains your
   project's ``conf.py``. If necessary this can be used to override the default discovery
   mechanism and force the server to use a folder of your choosing. Currently accepted
   values include:

   - ``/path/to/docs`` - An absolute path
   - ``${workspaceRoot}/docs`` - A path relative to the root of your workspace.

``sphinx.srcDir`` (string)
   The language server assumes that your project's ``srcDir`` (the folder containing your
   rst files) is the same as your projects's ``confDir``. If this assumption is not true,
   you can use this setting to tell the server where to look. Currently accepted values
   include:

   - ``/path/to/src/`` - An absolute path
   - ``${workspaceRoot}/docs/src`` - A path relative to the root of your workspace
   - ``${confDir}/../src/`` - A path relative to your project's ``confDir``

``sphinx.buildDir`` (string)
   By default the language server will choose a cache directory (as determined by
   `appdirs <https://pypi.org/project/appdirs>`_) to put Sphinx's build output.
   This option can be used to force the language server to use a location
   of your choosing, currently accepted values include:

   - ``/path/to/src/`` - An absolute path
   - ``${workspaceRoot}/docs/src`` - A path relative to the root of your workspace
   - ``${confDir}/../src/`` - A path relative to your project's ``confDir``

``server.logLevel`` (string)
   This can be used to set the level of log messages emitted by the server. This can be set
   to one of the following values.

   - ``error`` (default)
   - ``info``
   - ``debug``

``server.logFilter`` (string[])
   The language server will typically include log output from all of its components. This
   option can be used to restrict the log output to be only those named.

``server.hideSphinxOutput`` (boolean)
   Normally any build output from Sphinx will be forwarded to the client as log messages.
   If you prefer this flag can be used to exclude any Sphinx output from the log.

.. _VSCode Extension: https://github.com/swyddfa/esbonio/blob/4ce1ba426b85aa397d51336d8c7eecccb7516b71/code/src/lsp/client.ts#L253
