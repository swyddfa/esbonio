"""Default entry point, identical to calling ``python -m esbonio.lsp.sphinx``"""
import sys

from esbonio.cli import main
from esbonio.lsp.sphinx import cli

if __name__ == "__main__":
    sys.exit(main(cli))
