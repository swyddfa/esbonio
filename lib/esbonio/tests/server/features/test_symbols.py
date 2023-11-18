import pathlib
from typing import List
from typing import Optional

import pytest
from lsprotocol import types
from pytest_lsp import LanguageClient

from esbonio.server.testing import range_from_str


def symbol(
    name: str,
    kind: types.SymbolKind,
    range: str,
    selection_range: str = "",
    children: Optional[List[types.DocumentSymbol]] = None,
) -> types.DocumentSymbol:
    """Helper for defining symbol instances."""
    return types.DocumentSymbol(
        name=name,
        kind=kind,
        range=range_from_str(range),
        selection_range=range_from_str(selection_range or range),
        children=children or [],
    )


@pytest.mark.parametrize(
    "filepath, expected",
    [
        (["conf.py"], None),
        (
            ["theorems", "pythagoras.rst"],
            [
                symbol(
                    name="Pythagoras' Theorem",
                    kind=types.SymbolKind.String,
                    range="3:0-3:18",
                    children=[
                        symbol(
                            name=".. include:: ../math.rst",
                            kind=types.SymbolKind.Class,
                            range="8:0-8:23",
                        ),
                        symbol(
                            name=".. include:: /math.rst",
                            kind=types.SymbolKind.Class,
                            range="10:0-10:21",
                        ),
                        symbol(
                            name="Implementation",
                            kind=types.SymbolKind.String,
                            range="15:0-15:13",
                            children=[
                                symbol(
                                    name=".. module:: pythagoras",
                                    kind=types.SymbolKind.Class,
                                    range="20:0-20:21",
                                ),
                                symbol(
                                    name=".. currentmodule:: pythagoras",
                                    kind=types.SymbolKind.Class,
                                    range="22:0-22:28",
                                ),
                                symbol(
                                    name=".. data:: PI",
                                    kind=types.SymbolKind.Class,
                                    range="24:0-24:11",
                                ),
                                symbol(
                                    name=".. data:: UNKNOWN",
                                    kind=types.SymbolKind.Class,
                                    range="28:0-28:16",
                                ),
                                symbol(
                                    name=".. class:: Triangle(a: float, b: float, c: float)",
                                    kind=types.SymbolKind.Class,
                                    range="32:0-32:48",
                                    children=[
                                        symbol(
                                            name=".. attribute:: a",
                                            kind=types.SymbolKind.Class,
                                            range="36:0-36:15",
                                        ),
                                        symbol(
                                            name=".. attribute:: b",
                                            kind=types.SymbolKind.Class,
                                            range="40:0-40:15",
                                        ),
                                        symbol(
                                            name=".. attribute:: c",
                                            kind=types.SymbolKind.Class,
                                            range="44:0-44:15",
                                        ),
                                        symbol(
                                            name=".. method:: is_right_angled() -> bool",
                                            kind=types.SymbolKind.Class,
                                            range="48:0-48:36",
                                            children=[],
                                        ),
                                    ],
                                ),
                                symbol(
                                    name=".. function:: calc_hypotenuse(a: float, b: float) -> float",
                                    kind=types.SymbolKind.Class,
                                    range="53:0-53:57",
                                ),
                                symbol(
                                    name=".. function:: calc_side(c: float, b: float) -> float",
                                    kind=types.SymbolKind.Class,
                                    range="62:0-62:51",
                                ),
                                symbol(
                                    name=".. |rhs| replace:: right hand side",
                                    kind=types.SymbolKind.Class,
                                    range="71:0-71:33",
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
    ],
)
@pytest.mark.asyncio
@pytest.mark.skip
async def test_document_symbols(
    client: LanguageClient,
    uri_for,
    filepath: List[str],
    expected: Optional[List[types.DocumentSymbol]],
):
    """Ensure that we handle ``textDocument/documentSymbols`` requests correctly."""

    test_uri = uri_for("sphinx-default", "workspace", *filepath)
    test_path = pathlib.Path(test_uri)
    language_id = "restructuredtext" if test_path.suffix == ".rst" else "python"

    # Needed so that the server can inspect the language id of the document.
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=str(test_uri),
                language_id=language_id,
                version=0,
                text=test_path.read_text(),
            )
        )
    )

    actual = await client.text_document_document_symbol_async(
        types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )

    if expected is None:
        assert actual is None

    else:
        assert len(actual) == len(expected)
        for actual_symbol, expected_symbol in zip(actual, expected):
            check_symbols(actual_symbol, expected_symbol)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_diagnostics(client: LanguageClient, uri_for):
    """Ensure that the server reports any errors found by docutils when parsing the
    document."""

    test_uri = uri_for("sphinx-default", "workspace", "code", "cpp.rst")
    test_path = pathlib.Path(test_uri.fs_path)

    assert len(client.diagnostics.get(str(test_uri), [])) == 0

    # Needed so that the server can inspect the language id of the document.
    client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=str(test_uri),
                language_id="restructuredtext",
                version=0,
                text=test_path.read_text(),
            )
        )
    )

    symbols = await client.text_document_document_symbol_async(
        types.DocumentSymbolParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )
    assert symbols is not None and len(symbols) > 0

    diagnostics = client.diagnostics[str(test_uri)]
    assert len(diagnostics) == 4

    assert diagnostics[0] == types.Diagnostic(
        message="Definition list ends without a blank line; unexpected unindent.",
        source="docutils",
        severity=types.DiagnosticSeverity.Warning,
        range=types.Range(
            start=types.Position(line=18, character=0),
            end=types.Position(line=19, character=0),
        ),
    )

    assert diagnostics[1] == types.Diagnostic(
        message="Unexpected indentation.",
        source="docutils",
        severity=types.DiagnosticSeverity.Error,
        range=types.Range(
            start=types.Position(line=20, character=0),
            end=types.Position(line=21, character=0),
        ),
    )

    assert diagnostics[2] == types.Diagnostic(
        message="Block quote ends without a blank line; unexpected unindent.",
        source="docutils",
        severity=types.DiagnosticSeverity.Warning,
        range=types.Range(
            start=types.Position(line=22, character=0),
            end=types.Position(line=23, character=0),
        ),
    )

    assert diagnostics[3] == types.Diagnostic(
        message="Definition list ends without a blank line; unexpected unindent.",
        source="docutils",
        severity=types.DiagnosticSeverity.Warning,
        range=types.Range(
            start=types.Position(line=23, character=0),
            end=types.Position(line=24, character=0),
        ),
    )


def check_symbols(actual: types.DocumentSymbol, expected: types.DocumentSymbol):
    """Ensure that the given ``DocumentSymbols`` are equivalent."""

    assert isinstance(actual, types.DocumentSymbol)

    assert actual.name == expected.name
    assert actual.kind == expected.kind
    assert actual.range == expected.range
    assert actual.selection_range == expected.selection_range

    if expected.children is None:
        assert actual.children is None
        return

    assert actual.children is not None
    assert len(actual.children) == len(
        expected.children
    ), f"Children mismatch in symbol '{actual.name}'"

    for actual_child, expected_child in zip(actual.children, expected.children):
        check_symbols(actual_child, expected_child)
