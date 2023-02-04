import argparse
import logging
import sys
import warnings
from typing import Union

from pygls.protocol import default_converter

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore[assignment]


def esbonio_converter():
    converter = default_converter()
    converter.register_structure_hook(Union[Literal["auto"], int], lambda obj, _: obj)

    return converter


def setup_cli(progname: str, description: str) -> argparse.ArgumentParser:
    """Return an argument parser with the default command line options required for
    main.
    """

    cli = argparse.ArgumentParser(prog=f"python -m {progname}", description=description)
    cli.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="start a TCP instance of the language server listening on the given port.",
    )
    cli.add_argument(
        "--version", action="store_true", help="print the current version and exit."
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


def main(cli: argparse.ArgumentParser):
    """Standard main function for each of the default language servers."""

    # Put these here to avoid circular import issues.
    from esbonio.lsp import __version__
    from esbonio.lsp import create_language_server
    from esbonio.lsp.log import LOG_NAMESPACE
    from esbonio.lsp.log import MemoryHandler

    args = cli.parse_args()

    if args.version:
        print(f"v{__version__}")
        sys.exit(0)

    modules = list(args.modules)

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
        args.server_cls,
        modules,
        name="esbonio",
        version=__version__,
        # TODO: Figure out how to make this extensible
        converter_factory=esbonio_converter,
    )

    if args.port:
        server.start_tcp("localhost", args.port)
    else:
        server.start_io()
