from __future__ import annotations

import re
from urllib.parse import parse_qs

import pytest
import requests
from lsprotocol import types
from pytest_lsp import LanguageClient

from esbonio.server import Uri


@pytest.mark.asyncio(loop_scope="session")
async def test_preview(client: LanguageClient, uri_for):
    """Ensure that we can get ask the server to preview a given file for us."""

    workspace_uri = uri_for("workspaces", "demo")
    test_uri = workspace_uri / "rst" / "roles.rst"

    response = await client.workspace_execute_command_async(
        types.ExecuteCommandParams(
            command="esbonio.server.previewFile", arguments=[{"uri": str(test_uri)}]
        )
    )

    preview_uri = Uri.parse(response["uri"])

    assert preview_uri.scheme == "http"
    assert re.match(r"localhost:\d+", preview_uri.authority) is not None
    assert preview_uri.path == "/rst/roles.html"

    query_params = parse_qs(preview_uri.query)
    assert re.match(r"ws://localhost:\d+", query_params["ws"][0]) is not None

    # Check that the content looks ok
    response = requests.get(response["uri"])  # noqa: ASYNC210
    assert response.status_code == 200
    assert '<div id="esbonio-marker-index"' in response.text

    # See: https://github.com/swyddfa/esbonio/issues/1115
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"
