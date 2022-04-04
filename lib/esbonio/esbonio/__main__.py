"""Default entry point, identical to calling ``python -m esbonio.lsp.sphinx``"""
import sys

from esbonio import cli
from esbonio.lsp.sphinx import DEFAULT_MODULES
from esbonio.lsp.sphinx import SphinxLanguageServer

_cli = cli.setup_cli("esbonio", "Esbonio's Sphinx language server.")
_cli.set_defaults(modules=DEFAULT_MODULES)
_cli.set_defaults(server_cls=SphinxLanguageServer)


def main():
    cli.main(_cli)


if __name__ == "__main__":
    sys.exit(main())
