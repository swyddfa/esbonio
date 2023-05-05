import pathlib
from typing import List

import pygls.uris as uri
import pytest
from lsprotocol.types import DiagnosticSeverity
from lsprotocol.types import DocumentLink
from lsprotocol.types import DocumentLinkParams
from lsprotocol.types import Position
from lsprotocol.types import Range
from lsprotocol.types import TextDocumentIdentifier
from pytest_lsp import LanguageClient


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
                DocumentLink(
                    target="https://www.python.org/static/img/python-logo.png",
                    range=Range(
                        start=Position(line=11, character=11),
                        end=Position(line=11, character=60),
                    ),
                ),
            ],
        )
    ],
)
async def test_document_links(
    client: LanguageClient, uri: str, expected: List[DocumentLink]
):
    """Ensure that we handle ``textDocument/documentLink`` requests correctly."""

    test_uri = client.root_uri + uri
    links = await client.text_document_document_link_async(
        DocumentLinkParams(text_document=TextDocumentIdentifier(uri=test_uri))
    )

    expected_links = {link.target: link for link in expected}
    actual_links = {link.target: link for link in links}

    for target in expected_links:
        assert target in actual_links

        actual = actual_links.pop(target)
        assert expected_links[target].range == actual.range

    assert len(actual_links) == 0, f"Unexpected links {', '.join(actual_links.keys())}"


@pytest.mark.asyncio
async def test_docstring_diagnostics(client: LanguageClient):
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
async def test_included_diagnostics(client: LanguageClient):
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
