Editor Integrations
===================


.. toctree::
   :glob:
   :maxdepth: 1
   :hidden:

   *


This section contains notes on how to use the Language Server with various code editing
applications.


.. _editor_integration_common:

Common Setup
------------

The language server works by creating an instance of Sphinx's application object and
inspecting it in order to provide completion suggestions etc.  In order for this
application instance to have the correct configuration, the language server needs to be
installed into the same Python environment that you use when building your
documentation.

So the first step in integrating Esbonio with any editor is to ensure that the language
server has been installed into the correct environment. Unless you are using the
:ref:`editor_itegration_vscode` extension which attempts to automate this step for you,
this is something you'll have to do manually.

.. code-block:: console

   $ source .env/bin/activate
   (.env) $ pip install esbonio
