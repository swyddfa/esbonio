from __future__ import annotations

import argparse
import logging
import sys
import warnings
from logging.handlers import MemoryHandler

from pygls.protocol import default_converter

from esbonio.server import EsbonioLanguageServer
from esbonio.server import LSProtocol
from esbonio.server.features.log import LSPInfoFilter
from esbonio.server.setup import create_language_server


def setup_cli(commands: argparse._SubParsersAction):
    """Configure the cli commands provided by this module."""

    command = commands.add_parser("server", help="launch the esbonio language server")
    setup_cli_args(command)


def setup_cli_args(parser: argparse.ArgumentParser):
    _ = parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="start a TCP instance of the language server listening on the given port.",
    )

    modules = parser.add_argument_group(
        "modules", "include/exclude language server modules."
    )
    _ = modules.add_argument(
        "-i",
        "--include",
        metavar="MOD",
        action="append",
        default=[],
        dest="included_modules",
        help="include an additional module in the server configuration, can be given multiple times.",
    )
    _ = modules.add_argument(
        "-e",
        "--exclude",
        metavar="MOD",
        action="append",
        default=[],
        dest="excluded_modules",
        help="exclude a module from the server configuration, can be given multiple times.",
    )
    parser.set_defaults(run=run_server)


def run_server(args):
    """Run the language server."""

    # Order matters!
    modules = [
        "esbonio.server.features.log",
        "esbonio.server.features.project_manager",
        "esbonio.server.features.sphinx_manager",
        "esbonio.server.features.preview_manager",
        "esbonio.server.features.directives",
        "esbonio.server.features.roles",
        "esbonio.server.features.rst.directives",
        "esbonio.server.features.rst.roles",
        "esbonio.server.features.myst.directives",
        "esbonio.server.features.myst.roles",
        "esbonio.server.features.sphinx_support.diagnostics",
        "esbonio.server.features.sphinx_support.symbols",
        "esbonio.server.features.sphinx_support.directives",
        "esbonio.server.features.sphinx_support.roles",
    ]

    for mod in args.included_modules:
        modules.append(mod)

    for mod in args.excluded_modules:
        if mod in modules:
            modules.remove(mod)

    # Ensure we can capture warnings.
    logging.captureWarnings(True)

    if not sys.warnoptions:
        warnings.simplefilter("default")  # Enable capture of DeprecationWarnings

    # Setup a temporary logging handler that can cache messages until the language server
    # is ready to forward them onto the client.
    memory_handler = MemoryHandler(999999, flushLevel=logging.CRITICAL)
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[memory_handler],
    )

    server = create_language_server(
        EsbonioLanguageServer,
        modules,
        logger=logging.getLogger("esbonio"),
        protocol_cls=LSProtocol,
        converter_factory=default_converter,
    )
    memory_handler.addFilter(LSPInfoFilter(server))

    if args.port:
        server.start_tcp("localhost", args.port)
    else:
        server.start_io()
