To try the example configuration on your machine

#. Download :download:`init.vim <./editors/vim-lsp/init.vim>` to a folder
   of your choosing.

#. Ensure you have vim-plug's ``plug.vim`` file installed in your autoload
   directory. See `the documentation <https://github.com/junegunn/vim-plug#installation>`_
   for more details.

#. Open a terminal in the directory containing this file and run the
   following command to load this config isolated from your existing
   configuration::

    (n)vim -u init.vim

#. Install the required plugins::

    :PlugInstall
