import argparse
import logging
import sys
import warnings
from typing import Optional
from typing import Sequence

from pygls.protocol import default_converter

from .log import LOG_NAMESPACE
from .log import MemoryHandler
from .server import EsbonioLanguageServer
from .server import __version__
from .setup import create_language_server


def build_parser() -> argparse.ArgumentParser:
    """Return an argument parser with the default command line options required for
    main.
    """

    cli = argparse.ArgumentParser(description="The Esbonio language server")
    cli.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="start a TCP instance of the language server listening on the given port.",
    )
    cli.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="print the current version and exit.",
    )

    modules = cli.add_argument_group(
        "modules", "include/exclude language server modules."
    )
    modules.add_argument(
        "-i",
        "--include",
        metavar="MOD",
        action="append",
        default=[],
        dest="included_modules",
        help="include an additional module in the server configuration, can be given multiple times.",
    )
    modules.add_argument(
        "-e",
        "--exclude",
        metavar="MOD",
        action="append",
        default=[],
        dest="excluded_modules",
        help="exclude a module from the server configuration, can be given multiple times.",
    )

    return cli


def main(argv: Optional[Sequence[str]] = None):
    """Standard main function for each of the default language servers."""

    # Put these here to avoid circular import issues.

    cli = build_parser()
    args = cli.parse_args(argv)

    # Order matters!
    modules = [
        "esbonio.server.features.sphinx_manager",
        "esbonio.server.features.preview_manager",
        "esbonio.server.features.symbols",
    ]

    for mod in args.included_modules:
        modules.append(mod)

    for mod in args.excluded_modules:
        if mod in modules:
            modules.remove(mod)

    # Ensure we can capture warnings.
    logging.captureWarnings(True)
    warnlog = logging.getLogger("py.warnings")

    if not sys.warnoptions:
        warnings.simplefilter("default")  # Enable capture of DeprecationWarnings

    # Setup a temporary logging handler that can cache messages until the language server
    # is ready to forward them onto the client.
    logger = logging.getLogger(LOG_NAMESPACE)
    logger.setLevel(logging.DEBUG)

    handler = MemoryHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    warnlog.addHandler(handler)

    server = create_language_server(
        EsbonioLanguageServer,
        modules,
        logger=logger,
        converter_factory=default_converter,
    )

    if args.port:
        server.start_tcp("localhost", args.port)
    else:
        server.start_io()
