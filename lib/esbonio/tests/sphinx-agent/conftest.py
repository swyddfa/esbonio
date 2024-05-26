import logging
import pathlib
import sys

import pytest
import pytest_asyncio
from lsprotocol.types import WorkspaceFolder
from pygls.protocol import default_converter
from pygls.workspace import Workspace
from sphinx.application import Sphinx

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


@pytest.fixture
def build_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("build")


@pytest_asyncio.fixture
async def client(uri_for, build_dir):
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


@pytest.fixture
def app(client, uri_for, build_dir):
    """Sphinx application instance, used for validating results.

    While we don't use it directly, depending on the ``client`` fixture ensures that the build has
    completed and the ``environment.pickle`` file is there ready for us to use.
    """
    demo_workspace = uri_for("workspaces", "demo")
    return Sphinx(
        srcdir=demo_workspace.fs_path,
        confdir=demo_workspace.fs_path,
        outdir=str(pathlib.Path(build_dir, "html")),
        doctreedir=str(pathlib.Path(build_dir, "doctrees")),
        buildername="html",
    )


@pytest_asyncio.fixture
async def project(client: SubprocessSphinxClient):
    """The Sphinx project as captured by the database created by the Sphinx agent."""
    project = Project(client.db, default_converter())

    yield project
    await project.close()
