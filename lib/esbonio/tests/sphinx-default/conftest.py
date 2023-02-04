import asyncio
import os
import pathlib
import sys

import pygls.uris as uri
import pytest
import pytest_lsp
from pygls.protocol import default_converter
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient

from esbonio.lsp.sphinx import InitializationOptions
from esbonio.lsp.sphinx import SphinxServerConfig
from esbonio.lsp.testing import make_esbonio_client

root_path = pathlib.Path(__file__).parent / "workspace"

SERVER_CMD = ["-m", "esbonio"]
if "USE_DEBUGPY" in os.environ:
    SERVER_CMD = [
        "-m",
        "debugpy",
        "--listen",
        "localhost:5678",
        "--wait-for-client",
        *SERVER_CMD,
    ]

LOG_LEVEL = os.environ.get("SERVER_LOG_LEVEL", "error")


@pytest.fixture(scope="session")
def event_loop():
    # We need to redefine the event_loop fixture to match the scope of our
    # client_server fixture.
    #
    # https://github.com/pytest-dev/pytest-asyncio/issues/68#issuecomment-334083751

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def converter():
    return default_converter()


@pytest_lsp.fixture(
    scope="session",
    config=[
        ClientServerConfig(
            client="visual_studio_code",
            client_factory=make_esbonio_client,
            server_command=[sys.executable, *SERVER_CMD],
            initialization_options=InitializationOptions(
                server=SphinxServerConfig(log_level=LOG_LEVEL)
            ),
            root_uri=uri.from_fs_path(str(root_path)),
        ),
        ClientServerConfig(
            client="neovim",
            client_factory=make_esbonio_client,
            server_command=[sys.executable, *SERVER_CMD],
            initialization_options=InitializationOptions(
                server=SphinxServerConfig(log_level=LOG_LEVEL)
            ),
            root_uri=uri.from_fs_path(str(root_path)),
        ),
    ],
)
async def client(client_: LanguageClient):
    # Wait for the server to initialize.
    await client_.wait_for_notification("esbonio/buildComplete")
