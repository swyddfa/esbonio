import os
import pathlib
import sys

import pygls.uris as uri
import pytest
import pytest_lsp
from lsprotocol.types import InitializeParams
from pygls.protocol import default_converter
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient
from pytest_lsp import client_capabilities

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
def converter():
    return default_converter()


@pytest_lsp.fixture(
    scope="session",
    params=["visual_studio_code", "neovim"],
    config=ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, *SERVER_CMD],
    ),
)
async def client(request, lsp_client: LanguageClient):
    # Existing test cases depend on this being set.
    lsp_client.root_uri = uri.from_fs_path(str(root_path))

    await lsp_client.initialize_session(
        InitializeParams(
            capabilities=client_capabilities(request.param),
            initialization_options=InitializationOptions(
                server=SphinxServerConfig(log_level=LOG_LEVEL)
            ),
            root_uri=lsp_client.root_uri,
        )
    )

    # Wait for the server to initialize.
    await lsp_client.wait_for_notification("esbonio/buildComplete")

    yield

    # Teardown
    await lsp_client.shutdown_session()
