import pathlib
from typing import List

import pygls.uris as uri
import pytest
from pygls.lsp.types import DiagnosticSeverity
from pygls.lsp.types import DocumentLink
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pytest_lsp import check
from pytest_lsp import Client


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
async def test_docstring_diagnostics(client: Client):
    """Ensure that we can correctly reports errors in autodoc'd docstrings."""

    workspace_root = pathlib.Path(uri.to_fs_path(client.root_uri))

    expected_path = workspace_root / "code" / "diagnostics.py"
    expected_uri = uri.from_fs_path(str(expected_path))
    diagnostics = client.diagnostics[expected_uri]

    assert len(diagnostics) == 1
    actual = diagnostics[0]

    assert actual.severity == DiagnosticSeverity.Warning
    assert actual.message == "image file not readable: not-an-image.png"
    assert actual.source == "sphinx"
    assert actual.range == Range(
        start=Position(line=3, character=0), end=Position(line=4, character=0)
    )


@pytest.mark.asyncio
async def test_included_diagnostics(client: Client):
    """Ensure that we can correctly reports errors in `.. included::` files."""

    workspace_root = pathlib.Path(uri.to_fs_path(client.root_uri))

    expected_path = workspace_root / "sphinx-extensions" / "_include_me.txt"
    expected_uri = uri.from_fs_path(str(expected_path))
    diagnostics = client.diagnostics[expected_uri]

    assert len(diagnostics) == 1
    actual = diagnostics[0]

    assert actual.severity == DiagnosticSeverity.Warning
    assert actual.message == "image file not readable: not-a-valid-image-path.png"
    assert actual.source == "sphinx"
    assert actual.range == Range(
        start=Position(line=3, character=0), end=Position(line=4, character=0)
    )
