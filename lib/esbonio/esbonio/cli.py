import argparse
import sys

from esbonio.lsp import __version__
from esbonio.lsp import BUILTIN_MODULES
from esbonio.lsp import create_language_server
from esbonio.lsp import SphinxLanguageServer


def start_server(args):
    """Start the language server."""

    server = create_language_server(SphinxLanguageServer, BUILTIN_MODULES)

    if args.port:
        server.start_tcp("localhost", args.port)
    else:
        server.start_io()


cli = argparse.ArgumentParser(prog="esbonio", description="The Esbonio language server")

cli.add_argument(
    "-p",
    "--port",
    type=int,
    default=None,
    help="start a TCP instance of the language server listening on the given port ",
)

cli.add_argument(
    "--version", action="store_true", help="print the current version and exit"
)


def main():
    args = cli.parse_args()

    if args.version:
        print("v{}".format(__version__))
        sys.exit(0)

    start_server(args)
