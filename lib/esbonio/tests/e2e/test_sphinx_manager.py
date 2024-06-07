"""Technically, not a true end-to-end test as we're inspecting the internals of the server.
But since it depends on the sphinx agent, we may as well put it here."""

from __future__ import annotations

import asyncio
import io
import pathlib
import sys
import typing

import pytest
import pytest_asyncio
from lsprotocol import types as lsp
from pygls.server import StdOutTransportAdapter

from esbonio.server import EsbonioLanguageServer
from esbonio.server import Uri
from esbonio.server import create_language_server
from esbonio.server.features.project_manager import ProjectManager
from esbonio.server.features.sphinx_manager import ClientState
from esbonio.server.features.sphinx_manager import SphinxManager
from esbonio.server.features.sphinx_manager import make_subprocess_sphinx_client

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable
    from typing import Tuple

    ServerManager = Callable[[Any], Tuple[EsbonioLanguageServer, SphinxManager]]


@pytest.fixture
def demo_workspace(uri_for):
    return uri_for("workspaces", "demo")


@pytest.fixture
def docs_workspace(uri_for):
    return uri_for("..", "..", "..", "docs")


@pytest_asyncio.fixture()
async def server_manager(demo_workspace: Uri, docs_workspace):
    """An instance of the language server and sphinx manager to use for the test."""

    loop = asyncio.get_running_loop()

    esbonio = create_language_server(EsbonioLanguageServer, [], loop=loop)
    esbonio.lsp.transport = StdOutTransportAdapter(io.BytesIO(), sys.stderr.buffer)

    project_manager = ProjectManager(esbonio)
    esbonio.add_feature(project_manager)

    sphinx_manager = SphinxManager(
        make_subprocess_sphinx_client, project_manager, esbonio
    )
    esbonio.add_feature(sphinx_manager)

    def initialize(init_options):
        # Initialize the server.
        esbonio.lsp._procedure_handler(
            lsp.InitializeRequest(
                id=1,
                params=lsp.InitializeParams(
                    capabilities=lsp.ClientCapabilities(),
                    initialization_options=init_options,
                    workspace_folders=[
                        lsp.WorkspaceFolder(uri=str(demo_workspace), name="demo"),
                        lsp.WorkspaceFolder(uri=str(docs_workspace), name="docs"),
                    ],
                ),
            )
        )

        esbonio.lsp._procedure_handler(
            lsp.InitializedNotification(params=lsp.InitializedParams())
        )
        return esbonio, sphinx_manager

    yield initialize

    await sphinx_manager.shutdown(None)


@pytest.mark.asyncio
async def test_get_client(
    server_manager: ServerManager, demo_workspace: Uri, tmp_path: pathlib.Path
):
    """Ensure that we can create a SphinxClient correctly."""

    server, manager = server_manager(
        dict(
            esbonio=dict(
                sphinx=dict(
                    pythonCommand=[sys.executable],
                    buildCommand=["sphinx-build", "-M", "dirhtml", ".", str(tmp_path)],
                ),
            ),
        ),
    )
    # Ensure that the server is ready
    await server.ready

    result = await manager.get_client(demo_workspace / "index.rst")
    # At least for now, the first call to get_client will not return a client
    # but will instead "prime the system" ready to return a client the next
    # time it is called.
    assert result is None

    # Give the async tasks chance to complete.
    await asyncio.sleep(0.5)

    # A client should have been created and started
    client = manager.clients[str(demo_workspace)]

    assert client is not None
    assert client.state in {ClientState.Starting, ClientState.Running}

    # Now when we ask for the client, the client should be started and we should
    # get back the same instance
    result = await manager.get_client(demo_workspace / "index.rst")

    assert result is client
    assert client.state == ClientState.Running

    # And that the client initialized correctly
    assert client.builder == "dirhtml"
    assert client.src_uri == demo_workspace
    assert client.conf_uri == demo_workspace
    assert client.build_uri == Uri.for_file(tmp_path / "dirhtml")


@pytest.mark.asyncio
async def test_get_client_with_error(
    server_manager: ServerManager, demo_workspace: Uri
):
    """Ensure that we correctly handle the case where there is an error with a client."""

    server, manager = server_manager(None)
    # Ensure that the server is ready
    await server.ready

    result = await manager.get_client(demo_workspace / "index.rst")
    # At least for now, the first call to get_client will not return a client
    # but will instead "prime the system" ready to return a client the next
    # time it is called.
    assert result is None

    # Give the async tasks chance to complete.
    await asyncio.sleep(0.5)

    # A client should have been created and started
    client = manager.clients[str(demo_workspace)]

    assert client is not None
    assert client.state in {ClientState.Starting, ClientState.Errored}

    # Now when we ask for the client, the client should be started and we should
    # get back the same instance
    result = await manager.get_client(demo_workspace / "index.rst")

    assert result is client
    assert client.state == ClientState.Errored
    assert "No python environment configured" in str(client.exception)

    # Finally, if we request another uri from the same project we should get back
    # the same client instance - even though it failed to start.
    result = await manager.get_client(demo_workspace / "demo_myst.md")
    assert result is client


@pytest.mark.asyncio
async def test_get_client_with_many_uris(
    server_manager: ServerManager, demo_workspace: Uri, tmp_path: pathlib.Path
):
    """Ensure that when called in rapid succession, with many uris we only create a
    single client instance."""

    server, manager = server_manager(
        dict(
            esbonio=dict(
                sphinx=dict(
                    pythonCommand=[sys.executable],
                    buildCommand=["sphinx-build", "-M", "dirhtml", ".", str(tmp_path)],
                ),
            ),
        ),
    )

    # Ensure that the server is ready
    await server.ready

    src_uris = [Uri.for_file(f) for f in pathlib.Path(demo_workspace).glob("**/*.rst")]
    coros = [manager.get_client(s) for s in src_uris]

    # As with the other cases, this should only "prime" the system
    result = await asyncio.gather(*coros)
    assert all([r is None for r in result])

    # There should only have been one client created (in addition to the 'dummy' global
    # scoped client)
    assert len(manager.clients) == 2

    client = manager.clients[str(demo_workspace)]
    assert client is not None
    assert client.state is None

    # Now if we do the same again we should get the same client instance for each case.
    coros = [manager.get_client(s) for s in src_uris]
    result = await asyncio.gather(*coros)

    assert all([r is client for r in result])

    client = result[0]
    assert client.state == ClientState.Running

    # And that the client initialized correctly
    assert client.builder == "dirhtml"
    assert client.src_uri == demo_workspace
    assert client.conf_uri == demo_workspace
    assert client.build_uri == Uri.for_file(tmp_path / "dirhtml")


@pytest.mark.asyncio
async def test_get_client_with_many_uris_in_many_projects(
    server_manager: ServerManager,
    demo_workspace: Uri,
    docs_workspace: Uri,
    tmp_path: pathlib.Path,
):
    """Ensure that when called in rapid succession, with many uris we only create a
    single client instance for each project."""

    server, manager = server_manager(
        dict(
            esbonio=dict(
                sphinx=dict(pythonCommand=[sys.executable]),
                buildCommand=["sphinx-build", "-M", "dirhtml", ".", str(tmp_path)],
            ),
        ),
    )  # Ensure that the server is ready
    await server.ready

    src_uris = [Uri.for_file(f) for f in pathlib.Path(demo_workspace).glob("**/*.rst")]
    src_uris += [Uri.for_file(f) for f in pathlib.Path(docs_workspace).glob("**/*.rst")]
    coros = [manager.get_client(s) for s in src_uris]

    # As with the other cases, this should only "prime" the system
    result = await asyncio.gather(*coros)
    assert all([r is None for r in result])

    # There should only have been one client created for each project (in addition to
    # the 'dummy' global scoped client)
    assert len(manager.clients) == 3

    demo_client = manager.clients[str(demo_workspace)]
    assert demo_client is not None
    assert demo_client.state is None

    docs_client = manager.clients[str(docs_workspace)]
    assert docs_client is not None
    assert docs_client.state is None

    # Now if we do the same again we should get the same client instance for each case.
    coros = [manager.get_client(s) for s in src_uris]
    result = await asyncio.gather(*coros)

    assert all([(r is demo_client) or (r is docs_client) for r in result])

    assert demo_client.state == ClientState.Running

    # When run in CI, the docs won't have all the required dependencies available.
    assert docs_client.state in {ClientState.Running, ClientState.Errored}


@pytest.mark.asyncio
async def test_updated_config(
    server_manager: ServerManager, demo_workspace: Uri, tmp_path: pathlib.Path
):
    """Ensure that when the configuration affecting a Sphinx configuration is changed,
    the SphinxClient is recreated."""

    server, manager = server_manager(
        dict(
            esbonio=dict(
                sphinx=dict(
                    pythonCommand=[sys.executable],
                    buildCommand=["sphinx-build", "-M", "dirhtml", ".", str(tmp_path)],
                ),
            ),
        ),
    )
    # Ensure that the server is ready
    await server.ready

    result = await manager.get_client(demo_workspace / "index.rst")
    # At least for now, the first call to get_client will not return a client
    # but will instead "prime the system" ready to return a client the next
    # time it is called.
    assert result is None

    # Give the async tasks chance to complete.
    await asyncio.sleep(0.5)

    # A client should have been created and started
    client = manager.clients[str(demo_workspace)]

    assert client is not None
    assert client.state in {ClientState.Starting, ClientState.Running}

    # Now when we ask for the client, the client should be started and we should
    # get back the same instance
    result = await manager.get_client(demo_workspace / "index.rst")

    assert result is client
    assert client.state == ClientState.Running

    # And that the client initialized correctly
    assert client.builder == "dirhtml"

    # Now update the configuration
    server.configuration._initialization_options["esbonio"]["sphinx"][
        "buildCommand"
    ] = ["sphinx-build", "-M", "html", ".", str(tmp_path)]
    server.configuration._notify_subscriptions()

    # Give the async tasks chance to complete.
    await asyncio.sleep(0.5)

    # A new client should have been created, started and be using the new config
    new_client = manager.clients[str(demo_workspace)]

    assert new_client is not client
    assert new_client.state in {ClientState.Starting, ClientState.Running}

    # Ensure that the client has finished starting
    await new_client
    assert new_client.builder == "html"

    # The old client should have been stopped
    assert client.state == ClientState.Exited
