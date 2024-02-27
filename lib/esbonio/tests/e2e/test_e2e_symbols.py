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
            ["rst", "symbols.rst"],
            [
                document_symbol(
                    "Symbols",
                    types.SymbolKind.String,
                    "1:0-1:6",
                    children=[
                        document_symbol(
                            "What is a symbol?",
                            types.SymbolKind.Class,
                            "3:0-3:16",
                            detail="admonition",
                        ),
                        document_symbol(
                            "Document Symbols", types.SymbolKind.String, "14:0-14:15"
                        ),
                        document_symbol(
                            "Workspace Symbols", types.SymbolKind.String, "23:0-23:16"
                        ),
                    ],
                )
            ],
        ),
        (
            ["myst", "symbols.md"],
            [
                document_symbol(
                    "Symbols",
                    types.SymbolKind.String,
                    "0:0-0:6",
                    children=[
                        document_symbol(
                            "What is a symbol?",
                            types.SymbolKind.Class,
                            "2:0-2:16",
                            detail="admonition",
                        ),
                        document_symbol(
                            "Document Symbols",
                            types.SymbolKind.String,
                            "12:0-12:15",
                            children=[
                                document_symbol(
                                    "note",
                                    types.SymbolKind.Class,
                                    "20:0-20:3",
                                    detail="note",
                                ),
                            ],
                        ),
                        document_symbol(
                            "Workspace Symbols",
                            types.SymbolKind.String,
                            "27:0-27:16",
                        ),
                    ],
                )
            ],
        ),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_document_symbols(
    client: LanguageClient,
    uri_for,
    filepath: List[str],
    expected: Optional[List[types.DocumentSymbol]],
):
    """Ensure that we handle ``textDocument/documentSymbols`` requests correctly."""

    test_uri = uri_for("workspaces", "demo", *filepath)
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
                        "/rst/symbols.rst",
                        "1:0-1:6",
                        "Symbols",
                        types.SymbolKind.String,
                        "",
                    ),
                    (
                        "/rst/symbols.rst",
                        "3:0-3:16",
                        "What is a symbol? admonition",
                        types.SymbolKind.Class,
                        "Symbols",
                    ),
                    (
                        "/myst/symbols.md",
                        "0:0-0:6",
                        "Symbols",
                        types.SymbolKind.String,
                        "",
                    ),
                    (
                        "/myst/symbols.md",
                        "2:0-2:16",
                        "What is a symbol? admonition",
                        types.SymbolKind.Class,
                        "Symbols",
                    ),
                    (
                        "/myst/symbols.md",
                        "20:0-20:3",
                        "note",
                        types.SymbolKind.Class,
                        "Document Symbols",
                    ),
                ]
            ),
        ),
        # We should be able to query by symbol name
        (
            "Symbols",
            set(
                [
                    (
                        "/rst/symbols.rst",
                        "1:0-1:6",
                        "Symbols",
                        types.SymbolKind.String,
                        "",
                    ),
                    (
                        "/rst/symbols.rst",
                        "14:0-14:15",
                        "Document Symbols",
                        types.SymbolKind.String,
                        "Symbols",
                    ),
                    (
                        "/rst/symbols.rst",
                        "23:0-23:16",
                        "Workspace Symbols",
                        types.SymbolKind.String,
                        "Symbols",
                    ),
                    (
                        "/myst/symbols.md",
                        "0:0-0:6",
                        "Symbols",
                        types.SymbolKind.String,
                        "",
                    ),
                    (
                        "/myst/symbols.md",
                        "12:0-12:15",
                        "Document Symbols",
                        types.SymbolKind.String,
                        "Symbols",
                    ),
                    (
                        "/myst/symbols.md",
                        "27:0-27:16",
                        "Workspace Symbols",
                        types.SymbolKind.String,
                        "Symbols",
                    ),
                ]
            ),
        ),
        # We should also be able to query by (document) symbol `detail` e.g. a directive name
        (
            "admonition",
            set(
                [
                    (
                        "/myst/symbols.md",
                        "2:0-2:16",
                        "What is a symbol? admonition",
                        types.SymbolKind.Class,
                        "Symbols",
                    ),
                    (
                        "/rst/symbols.rst",
                        "3:0-3:16",
                        "What is a symbol? admonition",
                        types.SymbolKind.Class,
                        "Symbols",
                    ),
                ]
            ),
        ),
        # Make sure we don't return anything when there are no matches
        ("--not-a-real-symbol-name--", None),
    ],
)
@pytest.mark.asyncio(scope="session")
async def test_workspace_symbols(
    client: LanguageClient,
    query: str,
    uri_for,
    expected: Optional[Set[Tuple[str, str, str, types.SymbolKind, str]]],
):
    """Ensure that we handle ``workspace/symbol`` requests correctly."""

    workspace_uri = str(uri_for("workspaces", "demo"))
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
