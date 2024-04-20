import logging
import sys

import pytest
from lsprotocol.types import WorkspaceFolder
from pygls import IS_WIN
from pygls.workspace import Workspace

from esbonio.server.features.sphinx_manager.client import ClientState
from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)
from esbonio.server.features.sphinx_manager.client_subprocess import (
    make_test_sphinx_client,
)
from esbonio.server.features.sphinx_manager.config import SphinxConfig

logger = logging.getLogger("__name__")


@pytest.mark.asyncio
async def test_create_application(uri_for):
    """Ensure that we can create a Sphinx application instance correctly."""

    demo_workspace = uri_for("workspaces", "demo")
    test_uri = demo_workspace / "index.rst"

    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(uri=str(demo_workspace), name="demo"),
        ],
    )
    config = SphinxConfig(python_command=[sys.executable])
    resolved = config.resolve(test_uri, workspace, logger)
    assert resolved is not None
    client = None

    try:
        client = await make_test_sphinx_client(resolved)
        assert client.state == ClientState.Running

        info = client.sphinx_info
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
    finally:
        if client:
            await client.stop()


@pytest.mark.asyncio
async def test_create_application_error(uri_for, tmp_path_factory):
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
        python_command=[sys.executable],
        build_command=[
            "sphinx-build",
            "-b",
            "html",
            "-c",
            conf_dir,
            demo_workspace.fs_path,
            str(build_dir),
        ],
    )
    resolved = config.resolve(test_uri, workspace, logger)
    assert resolved is not None

    try:
        client = await SubprocessSphinxClient(resolved)
        assert client.state == ClientState.Errored

        message = "There is a programmable error in your configuration file:"
        assert message in str(client.exception)
    finally:
        await client.stop()
