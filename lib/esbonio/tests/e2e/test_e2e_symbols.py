from typing import List
from typing import Optional

import pytest
from lsprotocol import types
from pytest_lsp import LanguageClient

from esbonio.server.testing import range_from_str


def document_symbol(
    name: str,
    kind: types.SymbolKind,
    range: str,
    selection_range: str = "",
    children: Optional[List[types.DocumentSymbol]] = None,
    detail: str = "",
) -> types.DocumentSymbol:
    """Helper for defining symbol instances."""
    return types.DocumentSymbol(
        name=name,
        kind=kind,
        range=range_from_str(range),
        selection_range=range_from_str(selection_range or range),
        children=children or None,
        detail=detail,
    )


@pytest.mark.parametrize(
    "filepath, expected",
    [
        (["conf.py"], None),
        (
            ["theorems", "pythagoras.rst"],
            [
                document_symbol(
                    name="Pythagoras' Theorem",
                    kind=types.SymbolKind.String,
                    range="3:0-3:18",
                    children=[
                        document_symbol(
                            name="../math.rst",
                            detail=".. include::",
                            kind=types.SymbolKind.Class,
                            range="8:0-8:23",
                        ),
                        document_symbol(
                            name="/math.rst",
                            detail=".. include::",
                            kind=types.SymbolKind.Class,
                            range="10:0-10:21",
                        ),
                        document_symbol(
                            name="Implementation",
                            kind=types.SymbolKind.String,
                            range="15:0-15:13",
                            children=[
                                document_symbol(
                                    name="pythagoras",
                                    detail=".. module::",
                                    kind=types.SymbolKind.Class,
                                    range="20:0-20:21",
                                ),
                                document_symbol(
                                    name="pythagoras",
                                    detail=".. currentmodule::",
                                    kind=types.SymbolKind.Class,
                                    range="22:0-22:28",
                                ),
                                document_symbol(
                                    name="PI",
                                    detail=".. data::",
                                    kind=types.SymbolKind.Class,
                                    range="24:0-24:11",
                                ),
                                document_symbol(
                                    name="UNKNOWN",
                                    detail=".. data::",
                                    kind=types.SymbolKind.Class,
                                    range="28:0-28:16",
                                ),
                                document_symbol(
                                    name="Triangle(a: float, b: float, c: float)",
                                    detail=".. class::",
                                    kind=types.SymbolKind.Class,
                                    range="32:0-32:48",
                                    children=[
                                        document_symbol(
                                            name="a",
                                            detail=".. attribute::",
                                            kind=types.SymbolKind.Class,
                                            range="36:0-36:15",
                                        ),
                                        document_symbol(
                                            name="b",
                                            detail=".. attribute::",
                                            kind=types.SymbolKind.Class,
                                            range="40:0-40:15",
                                        ),
                                        document_symbol(
                                            name="c",
                                            detail=".. attribute::",
                                            kind=types.SymbolKind.Class,
                                            range="44:0-44:15",
                                        ),
                                        document_symbol(
                                            name="is_right_angled() -> bool",
                                            detail=".. method::",
                                            kind=types.SymbolKind.Class,
                                            range="48:0-48:36",
                                            children=[],
                                        ),
                                    ],
                                ),
                                document_symbol(
                                    name="calc_hypotenuse(a: float, b: float) -> float",
                                    detail=".. function::",
                                    kind=types.SymbolKind.Class,
                                    range="53:0-53:57",
                                ),
                                document_symbol(
                                    name="calc_side(c: float, b: float) -> float",
                                    detail="function::",
                                    kind=types.SymbolKind.Class,
                                    range="62:0-62:51",
                                ),
                                document_symbol(
                                    name="right hand side",
                                    detail=".. |rhs| replace::",
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
async def test_document_symbols(
    client: LanguageClient,
    uri_for,
    filepath: List[str],
    expected: Optional[List[types.DocumentSymbol]],
):
    """Ensure that we handle ``textDocument/documentSymbols`` requests correctly."""

    test_uri = uri_for("sphinx-default", "workspace", *filepath)
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
            check_document_symbol(actual_symbol, expected_symbol)


def check_document_symbol(actual: types.DocumentSymbol, expected: types.DocumentSymbol):
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
        check_document_symbol(actual_child, expected_child)
