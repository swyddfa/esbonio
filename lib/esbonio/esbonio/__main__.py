import argparse
import logging
import pathlib
import sys

import appdirs
import esbonio.lsp as lsp

from esbonio import __version__

LOG_LEVELS = [logging.ERROR, logging.INFO, logging.DEBUG]


def start_server(verbose):
    """Start the language server."""

    try:
        level = LOG_LEVELS[verbose]
    except IndexError:
        level = LOG_LEVELS[-1]

    logdir = pathlib.Path(appdirs.user_log_dir("esbonio", "swyddfa"))
    if not logdir.exists():
        logdir.mkdir(parents=True)

    logfile = logdir / "language_server.log"
    logging.basicConfig(
        level=level,
        format="[%(levelname)s][%(name)s]: %(message)s",
        filemode="w",
        filename=str(logfile),
    )

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
