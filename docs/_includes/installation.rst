.. note::

   The ``esbonio`` Python package **does not** need to be installed into the same environment as your project dependencies.
   A single, global installation is all that is required.

It's recommended to install the language server using a tool like `uv <https://docs.astral.sh/uv/>`__::

   uv tool install esbonio

or `pipx <https://pipx.pypa.io/stable/>`__::

   pipx install esbonio

Alternatively, you can use ``pip`` to install esbonio into a virtual environment of your choosing.
However you decide to install the server, the ``esbonio`` command must be available on your ``PATH``::

   $ esbonio --help
   usage: esbonio [-h] [--version] {server} ...

   The Esbonio language server

   options:
     -h, --help  show this help message and exit
     --version   print the current version and exit.

   commands:
     {server}
       server    launch the esbonio language server
