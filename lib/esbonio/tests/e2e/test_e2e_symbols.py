from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

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


@pytest.mark.parametrize(
    "query, expected",
    [
        # No query -> return all symbols.
        (
            "",
            set(
                [
                    # (
                    #   path (relative to workspace root),
                    #   range (s:c-e:c),
                    #   "name",
                    #   types.SymbolKind,
                    #   "container_name"
                    #  )
                    (
                        "/definitions.rst",
                        "21:0-21:43",
                        "/theorems/pythagoras.rst .. literalinclude::",
                        types.SymbolKind.Class,
                        "Definition Tests",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "3:0-3:18",
                        "Pythagoras' Theorem",
                        types.SymbolKind.String,
                        "",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "20:0-20:21",
                        "pythagoras .. module::",
                        types.SymbolKind.Class,
                        "Implementation",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "22:0-22:28",
                        "pythagoras .. currentmodule::",
                        types.SymbolKind.Class,
                        "Implementation",
                    ),
                    (
                        "/code/cpp.rst",
                        "5:0-5:33",
                        "bool isExample() .. cpp:function::",
                        types.SymbolKind.Class,
                        "ExampleClass",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "53:0-53:57",
                        "calc_hypotenuse(a: float, b: float) -> float .. function::",
                        types.SymbolKind.Class,
                        "Implementation",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "62:0-62:51",
                        "calc_side(c: float, b: float) -> float .. function::",
                        types.SymbolKind.Class,
                        "Implementation",
                    ),
                ]
            ),
        ),
        # We should be able to query by symbol name
        (
            "pythagoras",
            set(
                [
                    (
                        "/definitions.rst",
                        "21:0-21:43",
                        "/theorems/pythagoras.rst .. literalinclude::",
                        types.SymbolKind.Class,
                        "Definition Tests",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "3:0-3:18",
                        "Pythagoras' Theorem",
                        types.SymbolKind.String,
                        "",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "20:0-20:21",
                        "pythagoras .. module::",
                        types.SymbolKind.Class,
                        "Implementation",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "22:0-22:28",
                        "pythagoras .. currentmodule::",
                        types.SymbolKind.Class,
                        "Implementation",
                    ),
                ]
            ),
        ),
        # We should also be able to query by (document) symbol `detail` e.g. a directive name
        (
            "function::",
            set(
                [
                    (
                        "/code/cpp.rst",
                        "5:0-5:33",
                        "bool isExample() .. cpp:function::",
                        types.SymbolKind.Class,
                        "ExampleClass",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "53:0-53:57",
                        "calc_hypotenuse(a: float, b: float) -> float .. function::",
                        types.SymbolKind.Class,
                        "Implementation",
                    ),
                    (
                        "/theorems/pythagoras.rst",
                        "62:0-62:51",
                        "calc_side(c: float, b: float) -> float .. function::",
                        types.SymbolKind.Class,
                        "Implementation",
                    ),
                ]
            ),
        ),
        # Make sure we don't return anything when there are no matches
        ("--not-a-real-symbol-name--", None),
    ],
)
@pytest.mark.asyncio
async def test_workspace_symbols(
    client: LanguageClient,
    query: str,
    uri_for,
    expected: Optional[Set[Tuple[str, str, str, types.SymbolKind, str]]],
):
    """Ensure that we handle ``workspace/symbol`` requests correctly."""

    workspace_uri = str(uri_for("sphinx-default", "workspace"))
    result = await client.workspace_symbol_async(
        types.WorkspaceSymbolParams(query=query)
    )

    if expected is None:
        assert result is None
        return

    assert result is not None

    actual = set()
    for symbol in result:
        loc = symbol.location
        uri = loc.uri.replace(workspace_uri, "")

        actual.add(
            (uri, repr(loc.range), symbol.name, symbol.kind, symbol.container_name),
        )

    for symbol in expected:
        assert symbol in actual


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
