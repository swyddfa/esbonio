import logging
import sys

import pytest_asyncio
from lsprotocol.types import WorkspaceFolder
from pygls.workspace import Workspace

from esbonio.server.features.project_manager import Project
from esbonio.server.features.sphinx_manager.client import ClientState
from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)
from esbonio.server.features.sphinx_manager.client_subprocess import (
    make_test_sphinx_client,
)
from esbonio.server.features.sphinx_manager.config import SphinxConfig

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def client(uri_for, tmp_path_factory):
    build_dir = tmp_path_factory.mktemp("build")
    demo_workspace = uri_for("workspaces", "demo")
    test_uri = demo_workspace / "index.rst"

    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(uri=str(demo_workspace), name="demo"),
        ],
    )
    config = SphinxConfig(
        python_command=[sys.executable],
        build_command=[
            "sphinx-build",
            "-M",
            "html",
            demo_workspace.fs_path,
            str(build_dir),
        ],
    )
    resolved = config.resolve(test_uri, workspace, logger)
    assert resolved is not None

    sphinx_client = await make_test_sphinx_client(resolved)
    assert sphinx_client.state == ClientState.Running

    await sphinx_client.build()
    yield sphinx_client

    await sphinx_client.stop()


@pytest_asyncio.fixture
async def project(client: SubprocessSphinxClient):
    project = Project(client.db)

    yield project
    await project.close()
