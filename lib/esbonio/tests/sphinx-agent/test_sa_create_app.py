import logging
import sys

import pygls.uris as Uri
import pytest
from lsprotocol.types import WorkspaceFolder
from pygls.workspace import Workspace

from esbonio.server.features.sphinx_manager.client import SphinxClient
from esbonio.server.features.sphinx_manager.client import SphinxConfig
from esbonio.sphinx_agent import types


@pytest.fixture()
def sphinx_client():
    # TODO: Integrate with `pytest_lsp`
    logger = logging.getLogger("sphinx_client")
    logger.setLevel(logging.INFO)

    client = SphinxClient()

    @client.feature("window/logMessage")
    def _(params):
        logger.info("%s", params.message)

    return client


@pytest.mark.asyncio
async def test_create_application(sphinx_client, uri_for):
    """Ensure that we can create a Sphinx application instance correctly."""

    test_uri = uri_for("sphinx-default", "workspace", "index.rst")
    sd_workspace = uri_for("sphinx-default", "workspace")
    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(
                uri=uri_for("sphinx-extensions", "workspace"), name="sphinx-extensions"
            ),
            WorkspaceFolder(uri=sd_workspace, name="sphinx-default"),
        ],
    )
    config = SphinxConfig(python_command=[sys.executable])
    resolved = config.resolve(test_uri, workspace, sphinx_client.logger)
    assert resolved is not None

    try:
        await sphinx_client.start(resolved)
        assert not sphinx_client.stopped

        info = await sphinx_client.create_application(resolved)
        assert info is not None

        assert info.builder_name == "dirhtml"
        assert info.src_dir == Uri.to_fs_path(sd_workspace)
        assert info.conf_dir == Uri.to_fs_path(sd_workspace)
        assert "cache" in info.build_dir.lower()
    finally:
        if not sphinx_client.stopped:
            await sphinx_client.stop()
