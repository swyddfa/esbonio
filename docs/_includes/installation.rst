.. note::

   The ``esbonio`` Python package **does not** need to be installed into the same environment as your project dependencies.
   A single, global installation is all that is required.

It's recommended to install the language server using a tool like `uv <https://docs.astral.sh/uv/>`__::

   uv tool install --prerelease allow esbonio

or `pipx <https://pipx.pypa.io/stable/>`__::

   pipx install --pip-args='--pre' esbonio

Of course, you can use ``pip`` to install esbonio into a virtual environment of your choosing, the most important thing is that the ``esbonio`` command is available on your ``PATH``::

   $ esbonio --help
   usage: esbonio [-h] [-p PORT] [--version] [-i MOD] [-e MOD]

   The Esbonio language server

   options:
     -h, --help         show this help message and exit
     -p, --port PORT    start a TCP instance of the language server listening on the given port.
     --version          print the current version and exit.

   modules:
     include/exclude language server modules.

     -i, --include MOD  include an additional module in the server configuration, can be given multiple times.
     -e, --exclude MOD  exclude a module from the server configuration, can be given multiple times.
