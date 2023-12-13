import sys

import pytest_lsp
from lsprotocol.types import WorkspaceFolder
from pygls.workspace import Workspace
from pytest_lsp import ClientServerConfig

from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)
from esbonio.server.features.sphinx_manager.client_subprocess import (
    make_test_sphinx_client,
)
from esbonio.server.features.sphinx_manager.config import SphinxConfig


@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio.sphinx_agent"],
        client_factory=make_test_sphinx_client,
    ),
)
async def client(sphinx_client: SubprocessSphinxClient, uri_for, tmp_path_factory):
    build_dir = tmp_path_factory.mktemp("build")
    test_uri = uri_for("sphinx-default", "workspace", "index.rst")
    sd_workspace = uri_for("sphinx-default", "workspace")

    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(uri=str(sd_workspace), name="sphinx-default"),
        ],
    )
    config = SphinxConfig(
        build_command=[
            "sphinx-build",
            "-M",
            "html",
            sd_workspace.fs_path,
            str(build_dir),
        ],
    )
    resolved = config.resolve(test_uri, workspace, sphinx_client.logger)
    assert resolved is not None

    info = await sphinx_client.create_application(resolved)
    assert info is not None

    await sphinx_client.build()
    yield
