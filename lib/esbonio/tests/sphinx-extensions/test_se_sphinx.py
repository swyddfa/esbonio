import pathlib
import sys
from typing import List

import pygls.uris as uri
import pytest
from pygls.lsp.types import DiagnosticSeverity
from pygls.lsp.types import DocumentLink
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pytest_lsp import check
from pytest_lsp import Client
from pytest_lsp import ClientServerConfig
from pytest_lsp import make_client_server

from esbonio.lsp.testing import make_esbonio_client


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uri,expected",
    [
        (
            "/sphinx-extensions/definitions.rst",
            [
                DocumentLink(
                    target="https://docs.python.org/3.9/howto/logging.html#logging-basic-tutorial",
                    range=Range(
                        start=Position(line=5, character=29),
                        end=Position(line=5, character=58),
                    ),
                ),
                DocumentLink(
                    target="https://docs.python.org/3.9/library/logging.html#logging.Filter",
                    range=Range(
                        start=Position(line=7, character=19),
                        end=Position(line=7, character=40),
                    ),
                ),
                DocumentLink(
                    target="https://docs.python.org/3.9/howto/logging-cookbook.html",
                    range=Range(
                        start=Position(line=9, character=18),
                        end=Position(line=9, character=47),
                    ),
                ),
            ],
        )
    ],
)
async def test_document_links(client: Client, uri: str, expected: List[DocumentLink]):
    """Ensure that we handle ``textDocument/documentLink`` requests correctly."""

    test_uri = client.root_uri + uri
    links = await client.document_link_request(test_uri)

    assert len(links) == len(expected)

    for expected, actual in zip(expected, links):
        assert expected.range == actual.range
        assert expected.target == actual.target

    check.document_links(client, links)


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_docstring_diagnostics():
    """Ensure that we can correctly reports errors in autodoc'd docstrings."""

    # Setup, start with the file in the "good" state.
    workspace_root = pathlib.Path(__file__).parent / "workspace"

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=uri.from_fs_path(str(workspace_root)),
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)

    try:
        await test.start()
        await test.client.wait_for_notification("esbonio/buildComplete")

        expected_path = workspace_root / "code" / "diagnostics.py"
        expected_uri = uri.from_fs_path(str(expected_path))
        diagnostics = test.client.diagnostics[expected_uri]

        assert len(diagnostics) == 1
        actual = diagnostics[0]

        assert actual.severity == DiagnosticSeverity.Warning
        assert actual.message == "image file not readable: not-an-image.png"
        assert actual.source == "sphinx"
        assert actual.range == Range(
            start=Position(line=3, character=0), end=Position(line=4, character=0)
        )

    # Cleanup
    finally:
        await test.stop()
