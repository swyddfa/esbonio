import py.test
from pygls.lsp.types import DocumentSymbol
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import SymbolKind

from esbonio.lsp.testing import ClientServer
from esbonio.lsp.testing import document_symbols_request


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "filepath,expected",
    [
        ("conf.py", []),
        (
            "theorems/pythagoras.rst",
            [
                DocumentSymbol(
                    name="Pythagoras’ Theorem",
                    kind=SymbolKind.String,
                    range=Range(
                        start=Position(line=3, character=0),
                        end=Position(line=3, character=18),
                    ),
                    selection_range=Range(
                        start=Position(line=3, character=0),
                        end=Position(line=3, character=18),
                    ),
                    children=[
                        DocumentSymbol(
                            name="Implementation",
                            kind=SymbolKind.String,
                            range=Range(
                                start=Position(line=9, character=0),
                                end=Position(line=9, character=13),
                            ),
                            selection_range=Range(
                                start=Position(line=9, character=0),
                                end=Position(line=9, character=13),
                            ),
                            children=[],
                        )
                    ],
                )
            ],
        ),
    ],
)
async def test_document_symbols(client_server, filepath, expected):
    """Ensure that we handle ``textDocument/documentSymbols`` requests correctly"""

    test = await client_server("sphinx-default")  # type: ClientServer
    test_uri = test.server.workspace.root_uri + f"/{filepath}"

    results = await document_symbols_request(test=test, test_uri=test_uri)
    assert results == expected
