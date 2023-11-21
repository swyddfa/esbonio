import pathlib
import re
import sys

import pytest
import pytest_lsp
from lsprotocol.types import WorkspaceFolder
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
from esbonio.sphinx_agent import types


@pytest.mark.asyncio
async def test_build_includes_webview_js(client: SubprocessSphinxClient, uri_for):
    """Ensure that builds include the ``webview.js`` script."""

    out = client.build_uri
    src = client.src_uri
    assert out is not None and src is not None

    # Ensure the script is included in the build output
    webview_js = pathlib.Path(out / "_static" / "webview.js")
    assert webview_js.exists()
    assert "editor/scroll" in webview_js.read_text()

    # Ensure the script is included in the page
    index_html = pathlib.Path(out / "index.html")
    pattern = re.compile(r'<script src="_static/webview.js(\?v=[\w]+)?"></script>')
    assert pattern.search(index_html.read_text()) is not None


@pytest.mark.asyncio
async def test_diagnostics(client: SubprocessSphinxClient, uri_for):
    """Ensure that the sphinx agent reports diagnostics collected during the build"""
    expected = {
        uri_for("sphinx-default/workspace/definitions.rst").fs_path: [
            types.Diagnostic(
                message="unknown document: '/changelog'",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=13, character=0),
                    end=types.Position(line=14, character=0),
                ),
            ),
            types.Diagnostic(
                message="image file not readable: _static/bad.png",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=28, character=0),
                    end=types.Position(line=29, character=0),
                ),
            ),
        ],
        uri_for("sphinx-default/workspace/directive_options.rst").fs_path: [
            types.Diagnostic(
                message="document isn't included in any toctree",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=1, character=0),
                ),
            ),
            types.Diagnostic(
                message="image file not readable: filename.png",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=1, character=0),
                ),
            ),
        ],
    }
    result = await client.build()
    actual = {pathlib.Path(p): items for p, items in result.diagnostics.items()}

    actual_keys = set(actual.keys())
    expected_keys = set(pathlib.Path(k) for k in expected.keys())
    assert actual_keys == expected_keys

    for k, ex_diags in expected.items():
        # Order of results is not important
        assert set(actual[pathlib.Path(k)]) == set(ex_diags)


@pytest.mark.asyncio
async def test_build_content_override(client: SubprocessSphinxClient, uri_for):
    """Ensure that we can override the contents of a given src file when
    required."""

    out = client.build_uri
    src = client.src_uri
    assert out is not None and src is not None

    await client.build()

    # Before
    expected = "Welcome to the documentation!"
    index_html = pathlib.Path(out / "index.html")
    assert expected in index_html.read_text()

    await client.build(
        content_overrides={
            (src / "index.rst").fs_path: "My Custom Title\n==============="
        }
    )

    # Ensure the override was applied
    expected = "My Custom Title"
    print(index_html.read_text())
    assert expected in index_html.read_text()


@pytest_lsp.fixture(
    scope="module",
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio.sphinx_agent"],
        client_factory=make_test_sphinx_client,
    ),
)
async def client_build_error(
    sphinx_client: SubprocessSphinxClient, uri_for, tmp_path_factory
):
    """A sphinx client that will error when a build is triggered."""
    build_dir = tmp_path_factory.mktemp("build")
    test_uri = uri_for("sphinx-default", "workspace", "index.rst")
    sd_workspace = uri_for("sphinx-default", "workspace")

    workspace = Workspace(
        None,
        workspace_folders=[
            WorkspaceFolder(uri=str(sd_workspace), name="sphinx-default"),
        ],
    )

    conf_dir = uri_for("sphinx-default", "workspace-error-build").fs_path
    config = SphinxConfig(
        build_command=[
            "sphinx-build",
            "-b",
            "html",
            "-c",
            str(conf_dir),
            sd_workspace.fs_path,
            str(build_dir),
        ],
    )
    resolved = config.resolve(test_uri, workspace, sphinx_client.logger)
    assert resolved is not None

    info = await sphinx_client.create_application(resolved)
    assert info is not None

    yield


@pytest.mark.asyncio
async def test_build_error(client_build_error: SubprocessSphinxClient):
    """Ensure that when a build error occurs, useful information is reported."""

    with pytest.raises(
        JsonRpcInternalError, match="sphinx-build failed:.*division by zero.*"
    ):
        await client_build_error.build()
