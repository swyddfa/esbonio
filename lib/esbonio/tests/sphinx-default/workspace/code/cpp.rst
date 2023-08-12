C++
===

.. cpp:class:: ExampleClass

   .. cpp:function:: bool isExample()

      This method indicates whether or not it is an example


The following code block contains some exmapel lua code.

.. code-block:: lua

   lspconfig.esbonio.setup {
     init_options = {
       server = {
         logLevel = "debug"
       },
       sphinx = {
         confDir = "/path/to/docs",
         srcDir = "${confDir}/../docs-src"
       }
   }
