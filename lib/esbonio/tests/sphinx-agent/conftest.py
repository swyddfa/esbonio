import logging
import pathlib
import sys

import pytest
import pytest_asyncio
from lsprotocol.types import WorkspaceFolder
from pygls.protocol import default_converter
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
from esbonio.server.features.sphinx_manager.config import get_module_path
from esbonio.sphinx_agent.app import Sphinx

logger = logging.getLogger(__name__)


@pytest.fixture
def build_dir(tmp_path_factory):
    _dir = tmp_path_factory.mktemp("build")
    print(f"Using build dir: {_dir}")

    return _dir


@pytest_asyncio.fixture
async def client(request, uri_for, build_dir):
    demo_workspace = uri_for("workspaces", "demo")
    test_uri = demo_workspace / "index.rst"

    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(uri=str(demo_workspace), name="demo"),
        ],
    )
    config = SphinxConfig(
        enable_dev_tools=request.config.getoption("enable_devtools"),
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
def app(client, build_dir):
    """Sphinx application instance, used for validating results."""

    # In order to load the pickled envrionment correctly, we need to temporarily put
    # the parent directory of the `sphinx_agent` module on the path.
    path = get_module_path("esbonio.sphinx_agent")
    assert path is not None

    sys.path.insert(0, str(path))

    _app = Sphinx(
        srcdir=client.sphinx_info.src_dir,
        confdir=client.sphinx_info.conf_dir,
        outdir=str(pathlib.Path(build_dir, "html")),
        doctreedir=str(pathlib.Path(build_dir, "doctrees")),
        buildername="html",
    )

    sys.path.pop(0)

    return _app


@pytest_asyncio.fixture
async def project(client: SubprocessSphinxClient):
    """The Sphinx project as captured by the database created by the Sphinx agent."""
    project = Project(client.db, default_converter())

    yield project
    await project.close()
