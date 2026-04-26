from __future__ import annotations

import argparse
import asyncio
import logging
import pathlib
import sys
from functools import partial

from pygls.protocol import default_converter

from esbonio.server import EsbonioWorkspace
from esbonio.server import Uri
from esbonio.server.features.sphinx_manager import ClientState
from esbonio.server.features.sphinx_manager import SphinxClient
from esbonio.server.features.sphinx_manager import SphinxConfig
from esbonio.server.features.sphinx_manager import register_structure_hooks

try:
    import tomllib as toml
except ImportError:
    import tomli as toml  # type: ignore[no-redef]


def setup_cli(commands: argparse._SubParsersAction[argparse.ArgumentParser]):
    """Configure the cli commands provided by this module."""

    sphinx_cli = commands.add_parser("sphinx", help="interact with Sphinx projects")
    sphinx_cli.set_defaults(help_fn=sphinx_cli.print_help)

    _ = sphinx_cli.add_argument(
        "-c",
        "--config",
        default="pyproject.toml",
        type=pathlib.Path,
        help="set the path to the pyproject.toml file to use.",
    )
    sphinx_commands = sphinx_cli.add_subparsers(title="commands")

    build_cmd = sphinx_commands.add_parser("build", help="build a Sphinx project")
    setup_build_args(build_cmd)


def setup_build_args(parser: argparse.ArgumentParser):
    parser.set_defaults(run=sphinx_build)


async def handle_client(
    future: asyncio.Future[None],
    client: SphinxClient,
    old_state: ClientState,
    new_state: ClientState,
):
    if old_state == ClientState.Starting and new_state == ClientState.Running:
        _ = await client.build()

    if old_state == ClientState.Building and new_state == ClientState.Running:
        await client.stop()
        future.set_result(None)

    if new_state == ClientState.Errored:
        await client.stop()
        future.set_exception(client.exception)
        return


def load_config(path: pathlib.Path, logger: logging.Logger) -> SphinxConfig | None:
    config_uri = Uri.for_file(path)
    workspace = EsbonioWorkspace(root_uri=(config_uri / "..").as_string())

    converter = default_converter()
    register_structure_hooks(converter)

    data = toml.loads(path.read_text())
    values = data.get("tool", {}).get("esbonio", {}).get("sphinx", {})

    config = converter.structure(values, SphinxConfig)
    return config.resolve(config_uri, workspace, logger)


def get_sphinx_client(config: SphinxConfig, logger: logging.Logger):
    client = SphinxClient(config, logger=logger)

    @client.feature("$/progress")
    def _(params):
        pass

    return client


async def sphinx_build(args):
    """Run a Sphinx build including all of esbonio's extras, just as if it was running
    under the language server."""

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("[%(name)s]: %(message)s"))

    sphinx_log = logging.getLogger("sphinx")
    sphinx_log.setLevel(logging.INFO)
    sphinx_log.addHandler(handler)

    logger = logging.getLogger("esbonio")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    config = load_config(args.config.resolve(), logger)
    if config is None:
        print("Unable to generate a valid Sphinx configuration", file=sys.stderr)
        return 1

    client = get_sphinx_client(config, logger)

    future = asyncio.Future()
    client.add_listener("state-change", partial(handle_client, future))

    _ = await client.start()
    await asyncio.ensure_future(future)
