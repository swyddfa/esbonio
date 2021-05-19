import argparse
import sys

import esbonio.lsp as lsp

from esbonio.lsp import __version__


def start_server(args):
    """Start the language server."""

    server = lsp.create_language_server(lsp.BUILTIN_MODULES)

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

args = cli.parse_args()

if args.version:
    print("v{}".format(__version__))
    sys.exit(0)

start_server(args)
