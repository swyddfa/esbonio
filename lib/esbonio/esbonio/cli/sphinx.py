from __future__ import annotations

import argparse
import asyncio
import logging
import pathlib
import pdb  # noqa: T100
import shlex
import sys
import typing
from functools import partial

from pygls.protocol import default_converter

from esbonio.server import EsbonioWorkspace
from esbonio.server import Uri
from esbonio.server import merge_configs
from esbonio.server.features.sphinx_manager import ClientState
from esbonio.server.features.sphinx_manager import SphinxClient
from esbonio.server.features.sphinx_manager import SphinxConfig
from esbonio.server.features.sphinx_manager import register_structure_hooks

if typing.TYPE_CHECKING:
    from typing import Any

try:
    import tomllib as toml
except ImportError:
    import tomli as toml  # type: ignore[no-redef]


def setup_cli(commands: argparse._SubParsersAction[argparse.ArgumentParser]):
    """Configure the cli commands provided by this module."""

    sphinx_cli = commands.add_parser("sphinx", help="interact with sphinx projects")
    sphinx_cli.set_defaults(help_fn=sphinx_cli.print_help)

    _ = sphinx_cli.add_argument(
        "-c",
        "--config",
        default="pyproject.toml",
        type=pathlib.Path,
        help="set the path to the pyproject.toml file to use.",
    )
    sphinx_commands = sphinx_cli.add_subparsers(title="commands")

    build_cmd = sphinx_commands.add_parser(
        "build",
        help="build a sphinx project",
        description="""\
Build a sphinx project.

This command builds a sphinx project in the same manner as the esbonio language server,
meaning:

- Esbonio's additional sphinx extensions will be enabled
- Resulting html files will contain the HTML and JS necessary to support sync scrolling
- The esbonio.db file will be generated.

Useful as a debugging aid for compatibility issues.

In the absence of any additional command line flags, this command will look for a
pyproject.toml file in the current working directory and use the options in the
`[tool.esbonio.sphinx]` section to configure the build.

If the pyproject.toml file is not found, or does not contain the relevant options
this command will attempt to derive a valid configuration, following the same
rules as the language server.

Providing additional command line flags will override this behaviour.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    setup_build_args(build_cmd)


def setup_build_args(parser: argparse.ArgumentParser):
    """Configure the arguments for the build command."""
    parser.set_defaults(run=sphinx_build)

    _ = parser.add_argument(
        "--build-args",
        default=None,
        help="override the arguments passed to sphinx-build",
    )
    _ = parser.add_argument(
        "--python-cmd",
        default=None,
        help="override the python envrionment used",
    )
    _ = parser.add_argument(
        "--debug",
        action="store_true",
        help="attach a debugger to the build process (Python 3.14+)",
    )


async def handle_client(
    logger: logging.Logger,
    future: asyncio.Future[None],
    debug: bool,
    client: SphinxClient,
    old_state: ClientState,
    new_state: ClientState,
):
    if new_state == ClientState.Starting:
        if debug:
            try:
                logger.info("Attaching to build process...")
                pdb.attach(client.sphinx_pid)  # type: ignore[attr-defined]
            except RuntimeError as exc:
                await client.stop()
                logger.error("Unable to attach to build process: %s", exc)  # noqa: TRY400

    if old_state == ClientState.Starting and new_state == ClientState.Running:
        _ = await client.build()

    if old_state == ClientState.Building and new_state == ClientState.Running:
        await client.stop()
        future.set_result(None)

    if new_state == ClientState.Errored:
        await client.stop()
        future.set_exception(
            client.exception or RuntimeError("Client errored but no exception given")
        )
        return


def get_sphinx_config(
    path: pathlib.Path,
    build_args: str | None,
    python_cmd: str | None,
    logger: logging.Logger,
) -> SphinxConfig | None:
    """Return the SphinxConfig instance to use.

    This will attempt to read ``path`` as a pyproject.toml file and construct a
    ``SphinxConfig`` instance from the ``[tool.esbonio.sphinx]`` section. If the path
    does not exist this function will attempt to continue without it, any other error
    will lead to an abort.

    If additional parameters are given, they will override any values present in the config.

    Parameters
    ----------
    path
       The path to the ``pyproject.toml`` file to load configuration values from

    build_args
       If set, override ``esbonio.sphinx.buildArguments``.

    python_cmd
       If set, override ``esbonio.sphinx.pythonCommand``.

    logger
       The logger instance to use.

    Returns
    -------
    SphinxConfig
       The fully resolved SphinxConfig instance to use, ``None`` otherwise.
    """
    workspace = EsbonioWorkspace(root_uri=Uri.for_file(path.parent).as_string())

    converter = default_converter()
    register_structure_hooks(converter)

    defaults = {}
    if path.is_file():
        try:
            data = toml.loads(path.read_text())
            defaults = data.get("tool", {}).get("esbonio", {}).get("sphinx", {})
        except Exception:
            logging.exception("Unable to load configuration")
            return None

    overrides = {}
    if build_args is not None:
        overrides["buildArguments"] = shlex.split(build_args)

    if python_cmd is not None:
        overrides["pythonCommand"] = shlex.split(python_cmd)

    values = merge_configs(defaults, overrides)

    try:
        config = converter.structure(values, SphinxConfig)
    except Exception:
        logging.exception("Unable to parse configuration")
        return None

    config_uri = Uri.for_file(path)
    return config.resolve(config_uri, workspace, logger)


def get_sphinx_client(config: SphinxConfig, logger: logging.Logger):
    client = SphinxClient(config, logger=logger)

    @client.feature("$/progress")
    def _(params):
        pass

    return client


LOG_LEVELS = [
    logging.INFO,
    logging.DEBUG,
]


def setup_logging(args):
    # Sphinx output is handled separately.
    sphinx_handler = logging.StreamHandler()
    sphinx_handler.setLevel(logging.INFO)

    sphinx_log = logging.getLogger("sphinx")
    sphinx_log.setLevel(logging.INFO)
    sphinx_log.addHandler(sphinx_handler)

    try:
        log_level = LOG_LEVELS[args.verbose]
    except IndexError:
        log_level = LOG_LEVELS[-1]

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter("[%(name)s]: %(message)s"))

    logger = logging.getLogger("esbonio")
    logger.setLevel(log_level)
    logger.addHandler(handler)

    return logger


async def sphinx_build(args):
    """Run a Sphinx build including all of esbonio's extras, just as if it was running
    under the language server."""

    logger = setup_logging(args)

    if args.debug and sys.version_info < (3, 14):
        logger.error("--debug is only available on Python 3.14+")
        return

    config = get_sphinx_config(
        path=args.config.resolve(),
        build_args=args.build_args,
        python_cmd=args.python_cmd,
        logger=logger,
    )
    if config is None:
        logger.error("Unable to generate a valid Sphinx configuration")
        return 1

    client = get_sphinx_client(config, logger)

    future: asyncio.Future[Any] = asyncio.Future()
    client.add_listener(
        "state-change", partial(handle_client, logger, future, args.debug)
    )

    try:
        _ = await client.start()
        await asyncio.ensure_future(future)
        return 0
    except RuntimeError as exc:
        logger.error("%s", exc)  # noqa: TRY400
        return 1
    except Exception:
        logger.exception("Error occured during build")
        return 1
