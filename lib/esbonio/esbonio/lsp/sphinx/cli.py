"""Additional command line utilities for the SphinxLanguageServer."""
import argparse
import json
import sys
from typing import List

from esbonio.lsp.sphinx import SphinxConfig


def config_cmd(args, extra):

    if args.to_cli:
        config_to_cli(args.to_cli)
        return 0

    return cli_to_config(extra)


def config_to_cli(config: str):
    conf = SphinxConfig(**json.loads(config))
    print(" ".join(conf.to_cli_args()))
    return 0


def cli_to_config(cli_args: List[str]):
    conf = SphinxConfig.from_arguments(cli_args=cli_args)
    if conf is None:
        return 1

    print(json.dumps(conf.dict(by_alias=True), indent=2))
    return 0


cli = argparse.ArgumentParser(
    prog="esbonio-sphinx",
    description="Supporting commands and utilities for the SphinxLanguageServer.",
)
commands = cli.add_subparsers(title="commands")
config = commands.add_parser(
    "config",
    usage="%(prog)s [--from-cli] -- ARGS",
    description="configuration options helper.",
)
config.set_defaults(run=config_cmd)

mode = config.add_mutually_exclusive_group()
mode.add_argument(
    "--from-cli",
    action="store_true",
    default=True,
    help="convert sphinx-build cli options to esbonio's initialization options.",
)
mode.add_argument(
    "--to-cli",
    help="convert esbonio's initialization options to sphinx-build options",
)


def main():

    try:
        idx = sys.argv.index("--")
        args, extra = sys.argv[1:idx], sys.argv[idx + 1 :]
    except ValueError:
        args, extra = sys.argv[1:], None

    parsed_args = cli.parse_args(args)

    if hasattr(parsed_args, "run"):
        return parsed_args.run(parsed_args, extra)

    cli.print_help()


if __name__ == "__main__":
    sys.exit(main())
