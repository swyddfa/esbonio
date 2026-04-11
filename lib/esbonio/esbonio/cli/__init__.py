from __future__ import annotations

import argparse
import importlib
import logging
import typing

from esbonio.server import __version__

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

BUILTIN_COMMANDS = [
    "esbonio.cli.server",
]


def build_parser() -> argparse.ArgumentParser:
    """Return an argument parser with the default command line options required for
    main.
    """

    cli = argparse.ArgumentParser(description="The Esbonio language server")

    _ = cli.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="print the current version and exit.",
    )

    commands = cli.add_subparsers(title="commands")

    for module in BUILTIN_COMMANDS:
        load_command(commands, module)

    return cli


def load_command(commands: argparse._SubParsersAction, name: str):
    """Load the cli command(s) exposed by the given module name"""
    try:
        mod = importlib.import_module(name)
    except Exception:
        logger.exception("Unable to load commands from module '%s'\n", name)
        return

    if not hasattr(mod, "setup_cli"):
        logger.error(
            "Unable to load commands from module '%s': missing 'setup_cli' function",
            name,
        )
        return

    try:
        mod.setup_cli(commands)
    except Exception:
        logger.exception("Unable to load commands from module '%s'", name)
        return


def main(argv: Sequence[str] | None = None):
    cli = build_parser()
    args = cli.parse_args(argv)

    if hasattr(args, "run"):
        try:
            return args.run(args)
        except Exception:
            logger.exception("Error running command")
            return -1

    cli.print_help()
    return 0
