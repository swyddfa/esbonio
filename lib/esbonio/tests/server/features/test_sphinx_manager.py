import asyncio
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from lsprotocol import types as lsp
from pygls.exceptions import JsonRpcInternalError

from esbonio.server import EsbonioLanguageServer
from esbonio.server import EsbonioWorkspace
from esbonio.server import Uri
from esbonio.server.features.sphinx_manager import MockSphinxClient
from esbonio.server.features.sphinx_manager import SphinxConfig
from esbonio.server.features.sphinx_manager import SphinxManager
from esbonio.server.features.sphinx_manager import mock_sphinx_client_factory
from esbonio.sphinx_agent import types


@pytest.fixture()
def workspace(uri_for):
    return uri_for("sphinx-default", "workspace")


@pytest.fixture()
def progress():
    p = Mock()
    p.create_async = AsyncMock()
    return p


@pytest.fixture()
def server(event_loop, progress, workspace: Uri):
    """A mock instance of the language"""
    ready = asyncio.Future()
    ready.set_result(True)

    esbonio = EsbonioLanguageServer(loop=event_loop)
    esbonio._ready = ready
    esbonio.lsp.progress = progress
    esbonio.show_message = Mock()
    esbonio.configuration.get = Mock(return_value=SphinxConfig())
    esbonio.lsp._workspace = EsbonioWorkspace(
        None,
        workspace_folders=[lsp.WorkspaceFolder(str(workspace), "workspace")],
    )
    return esbonio


@pytest.fixture()
def sphinx_info(workspace: Uri):
    return types.SphinxInfo(
        id="123",
        version="6.0",
        conf_dir=workspace.fs_path,
        build_dir=(workspace / "_build" / "html").fs_path,
        builder_name="html",
        src_dir=workspace.fs_path,
    )


@pytest.mark.asyncio
async def test_create_application_error(server, workspace: Uri):
    """Ensure that we can handle errors during application creation correctly."""

    client = MockSphinxClient(JsonRpcInternalError("create sphinx application failed."))
    client_factory = mock_sphinx_client_factory(client)

    manager = SphinxManager(client_factory, server)

    result = await manager.get_client(workspace / "index.rst")
    assert result is None

    server.show_message.assert_called_with(
        "Unable to create sphinx application: create sphinx application failed.",
        lsp.MessageType.Error,
    )


@pytest.mark.asyncio
async def test_trigger_build_error(sphinx_info, server, workspace):
    """Ensure that we can handle build errors correctly."""

    client = MockSphinxClient(
        sphinx_info,
        build_file_map={(workspace / "index.rst").resolve(): "/"},
        build_result=JsonRpcInternalError("sphinx-build failed:"),
    )
    client_factory = mock_sphinx_client_factory()

    manager = SphinxManager(client_factory, server)
    manager.clients = {workspace: client}

    await manager.trigger_build(workspace / "index.rst")

    server.show_message.assert_called_with(
        "sphinx-build failed:", lsp.MessageType.Error
    )
