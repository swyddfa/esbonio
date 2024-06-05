from __future__ import annotations

import pathlib
import typing

import pytest
from lsprotocol import types
from pytest_lsp import LanguageClient

if typing.TYPE_CHECKING:
    from typing import Optional
    from typing import Set


EXPECTED = {
    "function",
    "module",
    "option",
    "program",
    "image",
    "toctree",
    "c:macro",
    "c:function",
    "py:function",
    "py:module",
    "std:program",
    "std:option",
}

RST_EXPECTED = EXPECTED.copy()
MYST_EXPECTED = {"eval-rst", *EXPECTED}

UNEXPECTED = {
    "macro",
    "restructuredtext-test-directive",
}

RST_UNEXPECTED = {"eval-rst", *UNEXPECTED}
MYST_UNEXPECTED = UNEXPECTED.copy()


@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        (".", None, None),
        ("..", RST_EXPECTED, RST_UNEXPECTED),
        (".. ", RST_EXPECTED, RST_UNEXPECTED),
        (".. d", RST_EXPECTED, RST_UNEXPECTED),
        (".. code-b", RST_EXPECTED, RST_UNEXPECTED),
        (".. codex-block:: ", None, None),
        (".. c:", RST_EXPECTED, RST_UNEXPECTED),
        (".. _some_label:", None, None),
        ("   .", None, None),
        ("   ..", RST_EXPECTED, RST_UNEXPECTED),
        ("   .. ", RST_EXPECTED, RST_UNEXPECTED),
        ("   .. d", RST_EXPECTED, RST_UNEXPECTED),
        ("   .. doctest:: ", None, None),
        ("   .. code-b", RST_EXPECTED, RST_UNEXPECTED),
        ("   .. codex-block:: ", None, None),
        ("   .. _some_label:", None, None),
        ("   .. c:", RST_EXPECTED, RST_UNEXPECTED),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_rst_directive_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: Optional[Set[str]],
    unexpected: Optional[Set[str]],
):
    """Ensure that the language server can offer directive completions in rst
    documents."""
    test_uri = uri_for("workspaces", "demo", "rst", "directives.rst")

    uri = str(test_uri)
    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()
    linum = contents.splitlines().index(".. Add your note here...")

    # Open the file
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=uri,
                language_id="restructuredtext",
                version=1,
                text=contents,
            )
        )
    )

    # Write some text
    #
    # This should replace the '.. Add your note here...' comment in
    # 'demo/rst/directives.rst' with the provided text
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[
                types.TextDocumentContentChangeEvent_Type1(
                    text=text,
                    range=types.Range(
                        start=types.Position(line=linum, character=0),
                        end=types.Position(line=linum + 1, character=0),
                    ),
                )
            ],
        )
    )

    # Make the completion request
    results = await client.text_document_completion_async(
        types.CompletionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=linum, character=len(text)),
        )
    )

    # Close the document - without saving!
    client.text_document_did_close(
        types.DidCloseTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
    )

    if expected is None:
        assert results is None
    else:
        items = {item.label for item in results.items}
        unexpected = unexpected or set()

        assert expected == items & expected
        assert set() == items & unexpected


@pytest.mark.parametrize(
    "text, expected, unexpected",
    [
        ("`", None, None),
        ("``", None, None),
        ("```", MYST_EXPECTED, MYST_UNEXPECTED),
        ("```{", MYST_EXPECTED, MYST_UNEXPECTED),
        ("```{d", MYST_EXPECTED, MYST_UNEXPECTED),
        ("```{code-b", MYST_EXPECTED, MYST_UNEXPECTED),
        ("```{codex-block} ", None, None),
        ("```{c:", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   `", None, None),
        ("   ``", None, None),
        ("   ```", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   ```{", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   ```{d", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   ```{doctest}", None, None),
        ("   ```{code-b", MYST_EXPECTED, MYST_UNEXPECTED),
        ("   ```{codex-block}", None, None),
        ("   ```{c:", MYST_EXPECTED, MYST_UNEXPECTED),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_myst_directive_completions(
    client: LanguageClient,
    uri_for,
    text: str,
    expected: Optional[Set[str]],
    unexpected: Optional[Set[str]],
):
    """Ensure that the language server can offer completions in MyST documents."""
    test_uri = uri_for("workspaces", "demo", "myst", "directives.md")

    uri = str(test_uri)
    fpath = pathlib.Path(test_uri)
    contents = fpath.read_text()
    linum = contents.splitlines().index("% Add your note here...")

    # Open the file
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=uri,
                language_id="markdown",
                version=1,
                text=contents,
            )
        )
    )

    # Write some text
    #
    # This should replace the '% Add your note here...' comment in
    # 'demo/myst/directives.md' with the provided text
    client.text_document_did_change(
        types.DidChangeTextDocumentParams(
            text_document=types.VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[
                types.TextDocumentContentChangeEvent_Type1(
                    text=text,
                    range=types.Range(
                        start=types.Position(line=linum, character=0),
                        end=types.Position(line=linum + 1, character=0),
                    ),
                )
            ],
        )
    )

    # Make the completion request
    results = await client.text_document_completion_async(
        types.CompletionParams(
            text_document=types.TextDocumentIdentifier(uri=uri),
            position=types.Position(line=linum, character=len(text)),
        )
    )

    # Close the document - without saving!
    client.text_document_did_close(
        types.DidCloseTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=uri)
        )
    )

    if expected is None:
        assert results is None
    else:
        items = {item.label for item in results.items}
        unexpected = unexpected or set()

        assert expected == items & expected
        assert set() == items & unexpected
