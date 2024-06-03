import logging
import pathlib
import sys

import pytest
import pytest_asyncio
from lsprotocol.types import WorkspaceFolder
from pygls.exceptions import JsonRpcInternalError
from pygls.workspace import Workspace

from esbonio.server.features.sphinx_manager.client import ClientState
from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)
from esbonio.server.features.sphinx_manager.client_subprocess import (
    make_test_sphinx_client,
)
from esbonio.server.features.sphinx_manager.config import SphinxConfig

logger = logging.getLogger(__name__)
STATIC_DIR = (
    pathlib.Path(__file__).parent.parent.parent / "esbonio" / "sphinx_agent" / "static"
).resolve()


@pytest.mark.asyncio
async def test_build_includes_webview_js(client: SubprocessSphinxClient, uri_for):
    """Ensure that builds include the ``webview.js`` script."""

    out = client.build_uri
    assert out is not None

    webview_js = STATIC_DIR / "webview.js"
    assert webview_js.exists()

    webview_script = webview_js.read_text()
    assert "editor/scroll" in webview_script

    # Ensure the script is included in the page
    index_html = pathlib.Path(out / "index.html")
    assert webview_script in index_html.read_text()


@pytest.mark.asyncio
async def test_build_content_override(client: SubprocessSphinxClient, uri_for):
    """Ensure that we can override the contents of a given src file when
    required."""

    out = client.build_uri
    src = client.src_uri
    assert out is not None and src is not None

    await client.build()

    # Before
    expected = "Welcome to the demo documentation"
    index_html = pathlib.Path(out / "index.html")
    assert expected in index_html.read_text()

    await client.build(
        content_overrides={str(src / "index.rst"): "My Custom Title\n==============="}
    )

    # Ensure the override was applied
    expected = "My Custom Title"
    print(index_html.read_text())
    assert expected in index_html.read_text()


@pytest_asyncio.fixture(scope="module")
async def client_build_error(uri_for, tmp_path_factory):
    """A sphinx client that will error when a build is triggered."""
    build_dir = tmp_path_factory.mktemp("build")
    demo_workspace = uri_for("workspaces", "demo")
    test_uri = demo_workspace / "index.rst"

    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(uri=str(demo_workspace), name="demo"),
        ],
    )

    conf_dir = uri_for("workspaces", "demo-error-build").fs_path
    config = SphinxConfig(
        python_command=[sys.executable],
        build_command=[
            "sphinx-build",
            "-b",
            "html",
            "-c",
            str(conf_dir),
            demo_workspace.fs_path,
            str(build_dir),
        ],
    )
    resolved = config.resolve(test_uri, workspace, logger)
    assert resolved is not None

    sphinx_client = await make_test_sphinx_client(resolved)
    assert sphinx_client.state == ClientState.Running

    yield sphinx_client

    await sphinx_client.stop()


@pytest.mark.asyncio(scope="module")
async def test_build_error(client_build_error: SubprocessSphinxClient):
    """Ensure that when a build error occurs, useful information is reported."""

    with pytest.raises(
        JsonRpcInternalError, match="sphinx-build failed:.*division by zero.*"
    ):
        await client_build_error.build()
