import json
from typing import Dict
from typing import List
from typing import Optional

from lsprotocol import types

from esbonio.server import EsbonioLanguageServer
from esbonio.server import LanguageFeature
from esbonio.server import Uri
from esbonio.server.features.sphinx_manager import SphinxManager


class SphinxSymbols(LanguageFeature):
    """Add support for ``textDocument/documentSymbol`` requests"""

    def __init__(self, server: EsbonioLanguageServer, manager: SphinxManager):
        super().__init__(server)
        self.manager = manager

    async def document_symbol(
        self, params: types.DocumentSymbolParams
    ) -> Optional[List[types.DocumentSymbol]]:
        """Called when a document symbols request it received."""

        uri = Uri.parse(params.text_document.uri)
        if (client := await self.manager.get_client(uri)) is None:
            return None

        symbols = await client.get_document_symbols(uri)
        if len(symbols) == 0:
            return None

        root: List[types.DocumentSymbol] = []
        index: Dict[int, types.DocumentSymbol] = {}

        for id_, name, kind, detail, range_json, parent_id, _ in symbols:
            range_ = self.converter.structure(json.loads(range_json), types.Range)
            symbol = types.DocumentSymbol(
                name=name,
                kind=self.converter.structure(kind, types.SymbolKind),
                range=range_,
                selection_range=range_,
                detail=detail,
            )

            index[id_] = symbol

            if parent_id is None:
                root.append(symbol)
            else:
                parent = index[parent_id]
                if parent.children is None:
                    parent.children = [symbol]
                else:
                    parent.children.append(symbol)

        return root


def esbonio_setup(server: EsbonioLanguageServer, sphinx_manager: SphinxManager):
    symbols = SphinxSymbols(server, sphinx_manager)
    server.add_feature(symbols)
