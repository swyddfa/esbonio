import pathlib
import re
import sys

import pytest
import pytest_lsp
from lsprotocol.types import WorkspaceFolder
from pygls import IS_WIN
from pygls.workspace import Workspace
from pytest_lsp import ClientServerConfig

from esbonio.server import Uri
from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)
from esbonio.server.features.sphinx_manager.client_subprocess import (
    make_test_sphinx_client,
)
from esbonio.server.features.sphinx_manager.config import SphinxConfig
from esbonio.sphinx_agent import types


@pytest_lsp.fixture(
    scope="module",
    params=["html", "dirhtml"],
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio.sphinx_agent"],
        client_factory=make_test_sphinx_client,
    ),
)
async def client(
    request, sphinx_client: SubprocessSphinxClient, uri_for, tmp_path_factory
):
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
        build_command=[
            "sphinx-build",
            "-M",
            request.param,
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
async def test_build_includes_webview_js(client: SubprocessSphinxClient, uri_for):
    """Ensure that builds include the ``webview.js`` script."""

    out = client.build_uri
    src = client.src_uri
    assert out is not None and src is not None

    await client.build()

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

    assert set(result.diagnostics.keys()) == set(expected.keys())

    for k, ex_diags in expected.items():
        # Order of results is not important
        assert set(result.diagnostics[k]) == set(ex_diags)


@pytest.mark.asyncio
async def test_build_file_map(client: SubprocessSphinxClient):
    """Ensure that we can trigger a Sphinx build correctly and the returned
    build_file_map is correct."""

    src = client.src_uri
    assert src is not None

    if client.builder == "dirhtml":
        build_file_map = {
            (src / "index.rst").fs_path: "",
            (src / "definitions.rst").fs_path: "definitions/",
            (src / "directive_options.rst").fs_path: "directive_options/",
            (src / "glossary.rst").fs_path: "glossary/",
            (src / "math.rst").fs_path: "theorems/pythagoras/",
            (src / "code" / "cpp.rst").fs_path: "code/cpp/",
            (src / "theorems" / "index.rst").fs_path: "theorems/",
            (src / "theorems" / "pythagoras.rst").fs_path: "theorems/pythagoras/",
            # It looks like non-existant files show up in this mapping as well
            (src / ".." / "badfile.rst").fs_path: "definitions/",
        }
    else:
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

    result = await client.build()

    # Paths are case insensitive on windows.
    if IS_WIN:
        actual_map = {f.lower(): uri for f, uri in result.build_file_map.items()}
        expected_map = {f.lower(): uri for f, uri in build_file_map.items()}
        assert actual_map == expected_map

        actual_uri_map = {
            Uri.parse(str(src).lower()): out
            for src, out in client.build_file_map.items()
        }
        expected_uri_map = {
            Uri.for_file(src.lower()): out for src, out in build_file_map.items()
        }
        assert actual_uri_map == expected_uri_map

    else:
        assert result.build_file_map == build_file_map

        build_uri_map = {Uri.for_file(src): out for src, out in build_file_map.items()}
        assert client.build_file_map == build_uri_map


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
