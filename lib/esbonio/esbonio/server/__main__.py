"""Equivalent to calling esbonio server through the top-level cli."""

import argparse
import logging
import sys

from esbonio.cli.server import setup_cli_args


def main():
    parser = argparse.ArgumentParser()
    setup_cli_args(parser)

    args = parser.parse_args()
    if hasattr(args, "run"):
        try:
            return args.run(args)
        except Exception:
            logging.exception("Error running command")
            return -1

    parser.print_help()
    return 0


sys.exit(main())
