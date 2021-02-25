import argparse
import logging
import sys

import esbonio.lsp as lsp

from esbonio import __version__
from esbonio.lsp import RstLanguageServer
from esbonio.lsp.logger import LspHandler

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "error": logging.ERROR,
    "info": logging.INFO,
}


class LogFilter:
    """A log filter that accepts message from any of the listed logger names."""

    def __init__(self, names):
        self.names = names

    def filter(self, record):
        return any(record.name == name for name in self.names)


def configure_logging(args, server: RstLanguageServer):

    level = LOG_LEVELS[args.log_level]

    lsp_logger = logging.getLogger("esbonio.lsp")
    lsp_logger.setLevel(level)

    lsp_handler = LspHandler(server)
    lsp_handler.setLevel(level)

    if args.log_filter is not None:
        lsp_handler.addFilter(LogFilter(args.log_filter))

    formatter = logging.Formatter("[%(name)s] %(message)s")
    lsp_handler.setFormatter(formatter)
    lsp_logger.addHandler(lsp_handler)

    if not args.hide_sphinx_output:
        sphinx_logger = logging.getLogger("esbonio.sphinx")
        sphinx_logger.setLevel(logging.INFO)

        sphinx_handler = LspHandler(server)
        sphinx_handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(message)s")
        sphinx_handler.setFormatter(formatter)
        sphinx_logger.addHandler(sphinx_handler)


def start_server(args):
    """Start the language server."""

    server = lsp.create_language_server(lsp.BUILTIN_MODULES, cache_dir=args.cache_dir)
    configure_logging(args, server)

    if args.port:
        server.start_tcp("localhost", args.port)
    else:
        server.start_io()


cli = argparse.ArgumentParser(prog="esbonio", description="The Esbonio language server")

cli.add_argument(
    "--cache-dir",
    default=None,
    type=str,
    help="the directory where cached data should be stored, e.g. Sphinx build output ",
)

cli.add_argument(
    "--hide-sphinx-output",
    action="store_true",
    help="hide sphinx build output from the log",
)

cli.add_argument(
    "--log-filter",
    action="append",
    help="only include log messages from loggers with the given name,"
    + "can be set multiple times.",
)

cli.add_argument(
    "--log-level",
    choices=["error", "info", "debug"],
    default="error",
    help="set the level of log message to show from the language server",
)

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
