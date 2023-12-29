import sys

import pytest
import pytest_lsp
from lsprotocol.types import WorkspaceFolder
from pygls import IS_WIN
from pygls.exceptions import JsonRpcInternalError
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
    )
)
async def client(sphinx_client: SubprocessSphinxClient):
    yield


@pytest.mark.asyncio
async def test_create_application(client: SubprocessSphinxClient, uri_for):
    """Ensure that we can create a Sphinx application instance correctly."""

    demo_workspace = uri_for("workspaces", "demo")
    test_uri = demo_workspace / "index.rst"

    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(uri=str(demo_workspace), name="demo"),
        ],
    )
    config = SphinxConfig()
    resolved = config.resolve(test_uri, workspace, client.logger)
    assert resolved is not None

    info = await client.create_application(resolved)
    assert info is not None
    assert info.builder_name == "dirhtml"

    # Paths are case insensitive on Windows
    if IS_WIN:
        assert info.src_dir.lower() == demo_workspace.fs_path.lower()
        assert info.conf_dir.lower() == demo_workspace.fs_path.lower()
        assert "cache" in info.build_dir.lower()
    else:
        assert info.src_dir == demo_workspace.fs_path
        assert info.conf_dir == demo_workspace.fs_path
        assert "cache" in info.build_dir


@pytest.mark.asyncio
async def test_create_application_error(
    client: SubprocessSphinxClient, uri_for, tmp_path_factory
):
    """Ensure that we can handle errors during application creation."""

    build_dir = tmp_path_factory.mktemp("build")
    demo_workspace = uri_for("workspaces", "demo")
    test_uri = demo_workspace / "index.rst"

    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(uri=str(demo_workspace), name="demo"),
        ],
    )

    conf_dir = uri_for("workspaces", "demo-error").fs_path
    config = SphinxConfig(
        build_command=[
            "sphinx-build",
            "-b",
            "html",
            "-c",
            conf_dir,
            demo_workspace.fs_path,
            str(build_dir),
        ]
    )
    resolved = config.resolve(test_uri, workspace, client.logger)
    assert resolved is not None

    with pytest.raises(
        JsonRpcInternalError,
        match="There is a programmable error in your configuration file:",
    ):
        await client.create_application(resolved)
