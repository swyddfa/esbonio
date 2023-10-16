import pathlib
import sys

import pytest_lsp
from lsprotocol import types
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient
from pytest_lsp import client_capabilities

# Disable the sphinx integration - at least for now...
SERVER_CMD = [
    "-m",
    "esbonio.server",
    "--exclude",
    "esbonio.server.features.sphinx_manager",
]
TEST_DIR = pathlib.Path(__file__).parent.parent


@pytest_lsp.fixture(
    scope="session",
    params=["visual_studio_code", "neovim"],
    config=ClientServerConfig(
        server_command=[sys.executable, *SERVER_CMD],
    ),
)
async def client(request, uri_for, lsp_client: LanguageClient):
    workspace_uri = uri_for("sphinx-default", "workspace")

    await lsp_client.initialize_session(
        types.InitializeParams(
            capabilities=client_capabilities(request.param),
            initialization_options={"server": {"logLevel": "debug"}},
            workspace_folders=[
                types.WorkspaceFolder(uri=str(workspace_uri), name="sphinx-default"),
            ],
        )
    )

    yield

    # Teardown
    await lsp_client.shutdown_session()
