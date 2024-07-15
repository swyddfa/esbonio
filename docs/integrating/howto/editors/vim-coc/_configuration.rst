The language server provides a number of configuration
values which can be set in coc.nvim's ``coc-settings.json`` configuration file, for
example

.. code-block:: json

   {
     "esbonio.sphinx.confDir": "${workspaceRoot}/docs",
     "esbonio.sphinx.srcDir": "${confDir}/../src"
   }

See coc.nvim's `documentation <https://github.com/neoclide/coc.nvim/wiki/Using-the-configuration-file>`_
for more details on its configuration.

The following is a list of all the available options, note in ``coc-esbonio`` they
require an ``esbonio.*`` prefix.
