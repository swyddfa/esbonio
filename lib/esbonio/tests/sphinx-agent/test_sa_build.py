import logging
import sys

import pytest
import pytest_asyncio
from lsprotocol.types import WorkspaceFolder
from pygls.workspace import Workspace

from esbonio.server import Uri
from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)
from esbonio.server.features.sphinx_manager.config import SphinxConfig


@pytest_asyncio.fixture(scope="module")
async def sphinx_client(uri_for, tmp_path_factory):
    # TODO: Integrate with `pytest_lsp`
    logger = logging.getLogger("sphinx_client")
    logger.setLevel(logging.INFO)

    client = SubprocessSphinxClient()

    @client.feature("window/logMessage")
    def _(params):
        logger.info("%s", params.message)

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
        build_command=["sphinx-build", "-M", "html", ".", str(build_dir)],
        python_command=[sys.executable],
        env_passthrough=["PYTHONPATH"],
    )
    resolved = config.resolve(test_uri, workspace, client.logger)
    assert resolved is not None

    info = await client.create_application(resolved)
    assert info is not None

    yield client

    if not client.stopped:
        await client.stop()


@pytest.mark.asyncio
async def test_build_file_map(sphinx_client, uri_for):
    """Ensure that we can trigger a Sphinx build correctly and the returned
    build_file_map is correct."""

    src = sphinx_client.src_uri
    assert src is not None

    build_file_map = {
        (src / "index.rst").fs_path: "index.html",
        (src / "definitions.rst").fs_path: "definitions.html",
        (src / "directive_options.rst").fs_path: "directive_options.html",
        (src / "glossary.rst").fs_path: "glossary.html",
        (src / "math.rst").fs_path: "theorems/pythagoras.html",
        (src / "code" / "cpp.rst").fs_path: "code/cpp.html",
        (src / "theorems" / "index.rst").fs_path: "theorems/index.html",
        (src / "theorems" / "pythagoras.rst").fs_path: "theorems/pythagoras.html",
        # It looks like non-existant files show up in this mapping as well
        (src / ".." / "badfile.rst").fs_path: "definitions.html",
    }

    result = await sphinx_client.build()
    assert result.build_file_map == build_file_map

    build_uri_map = {Uri.for_file(src): out for src, out in build_file_map.items()}
    assert sphinx_client.build_file_map == build_uri_map
