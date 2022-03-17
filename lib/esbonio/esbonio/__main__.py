"""Default entry point, identical to calling ``python -m esbonio.lsp.sphinx``"""
import sys

from esbonio.cli import main
from esbonio.cli import setup_cli
from esbonio.lsp.sphinx import DEFAULT_MODULES
from esbonio.lsp.sphinx import SphinxLanguageServer

cli = setup_cli("esbonio", "Esbonio's Sphinx language server.")
cli.set_defaults(modules=DEFAULT_MODULES)
cli.set_defaults(server_cls=SphinxLanguageServer)

if __name__ == "__main__":
    sys.exit(main(cli))
