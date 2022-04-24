from typing import List
from typing import Optional

import py.test
from pygls.lsp.types import DocumentSymbol
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import SymbolKind
from pytest_lsp import Client


def from_str(spec: str):
    """Create a range from the given string a:b-x:y"""
    start, end = spec.split("-")
    sl, sc = start.split(":")
    el, ec = end.split(":")

    return Range(
        start=Position(line=int(sl), character=int(sc)),
        end=Position(line=int(el), character=int(ec)),
    )


def symbol(
    name: str,
    kind: SymbolKind,
    range: str,
    selection_range: str = "",
    children: Optional[List[DocumentSymbol]] = None,
) -> DocumentSymbol:
    """Helper for writing symbols."""
    return DocumentSymbol(
        name=name,
        kind=kind,
        range=from_str(range),
        selection_range=from_str(selection_range or range),
        children=children or [],
    )


@py.test.mark.parametrize(
    "filepath,expected",
    [
        ("conf.py", []),
        (
            "theorems/pythagoras.rst",
            [
                symbol(
                    name="Pythagoras' Theorem",
                    kind=SymbolKind.String,
                    range="3:0-3:18",
                    children=[
                        symbol(
                            name=".. include:: ../math.rst",
                            kind=SymbolKind.Class,
                            range="8:0-8:23",
                        ),
                        symbol(
                            name=".. include:: /math.rst",
                            kind=SymbolKind.Class,
                            range="10:0-10:21",
                        ),
                        symbol(
                            name="Implementation",
                            kind=SymbolKind.String,
                            range="15:0-15:13",
                            children=[
                                symbol(
                                    name=".. module:: pythagoras",
                                    kind=SymbolKind.Class,
                                    range="20:0-20:21",
                                ),
                                symbol(
                                    name=".. currentmodule:: pythagoras",
                                    kind=SymbolKind.Class,
                                    range="22:0-22:28",
                                ),
                                symbol(
                                    name=".. data:: PI",
                                    kind=SymbolKind.Class,
                                    range="24:0-24:11",
                                ),
                                symbol(
                                    name=".. data:: UNKNOWN",
                                    kind=SymbolKind.Class,
                                    range="28:0-28:16",
                                ),
                                symbol(
                                    name=".. class:: Triangle(a: float, b: float, c: float)",
                                    kind=SymbolKind.Class,
                                    range="32:0-32:48",
                                    children=[
                                        symbol(
                                            name=".. attribute:: a",
                                            kind=SymbolKind.Class,
                                            range="36:0-36:15",
                                        ),
                                        symbol(
                                            name=".. attribute:: b",
                                            kind=SymbolKind.Class,
                                            range="40:0-40:15",
                                        ),
                                        symbol(
                                            name=".. attribute:: c",
                                            kind=SymbolKind.Class,
                                            range="44:0-44:15",
                                        ),
                                        symbol(
                                            name=".. method:: is_right_angled() -> bool",
                                            kind=SymbolKind.Class,
                                            range="48:0-48:36",
                                            children=[],
                                        ),
                                    ],
                                ),
                                symbol(
                                    name=".. function:: calc_hypotenuse(a: float, b: float) -> float",
                                    kind=SymbolKind.Class,
                                    range="53:0-53:57",
                                ),
                                symbol(
                                    name=".. function:: calc_side(c: float, b: float) -> float",
                                    kind=SymbolKind.Class,
                                    range="62:0-62:51",
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
    ],
)
async def test_document_symbols(client: Client, filepath: str, expected):
    """Ensure that we handle ``textDocument/documentSymbols`` requests correctly"""

    test_uri = client.root_uri + f"/{filepath}"
    symbols = await client.document_symbols_request(test_uri)

    assert symbols == expected
