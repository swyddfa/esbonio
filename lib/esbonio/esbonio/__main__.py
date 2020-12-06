import argparse
import logging
import sys

import esbonio.lsp as lsp

from esbonio import __version__
from esbonio.lsp.logger import LspHandler

LOG_LEVELS = [logging.ERROR, logging.INFO, logging.DEBUG]


def configure_logging(verbose, server):

    try:
        level = LOG_LEVELS[-1]
    except IndexError:
        level = LOG_LEVELS[-1]

    lsp_logger = logging.getLogger("esbonio.lsp")
    lsp_logger.setLevel(level)

    lsp_handler = LspHandler(server)
    lsp_handler.setLevel(level)

    formatter = logging.Formatter("[%(name)s] %(message)s")
    lsp_handler.setFormatter(formatter)
    lsp_logger.addHandler(lsp_handler)

    sphinx_logger = logging.getLogger("esbonio.sphinx")
    sphinx_logger.setLevel(level)

    sphinx_handler = LspHandler(server)
    sphinx_handler.setLevel(level)

    formatter = logging.Formatter("%(message)s")
    sphinx_handler.setFormatter(formatter)
    sphinx_logger.addHandler(sphinx_handler)


def start_server(verbose):
    """Start the language server."""

    configure_logging(verbose, lsp.server)
    lsp.server.start_io()


cli = argparse.ArgumentParser(prog="esbonio", description="The Esbonio language server")
cli.add_argument(
    "--version", action="store_true", help="print the current version and exit"
)
cli.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="increase output verbosity, repeatable e.g. -v, -vv, -vvv, ...",
)


args = cli.parse_args()

if args.version:
    print("v{}".format(__version__))
    sys.exit(0)

start_server(args.verbose)
