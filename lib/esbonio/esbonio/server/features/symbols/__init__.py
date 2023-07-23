from typing import List
from typing import Optional

from lsprotocol import types

from esbonio.server import EsbonioLanguageServer
from esbonio.server.feature import LanguageFeature

from .io import read_initial_doctree
from .visitor import SymbolVisitor


class DocumentSymbols(LanguageFeature):
    """Handles document symbol requests."""

    def document_symbol(
        self, params: types.DocumentSymbolParams
    ) -> Optional[List[types.DocumentSymbol]]:
        uri = params.text_document.uri
        doc = self.server.workspace.get_document(uri)

        try:
            doctree = read_initial_doctree(doc, self.logger)
        except Exception:
            self.logger.error("Unable to parse doctree", exc_info=True)
            return None

        if doctree is None:
            return None

        visitor = SymbolVisitor(self.logger, doctree)
        doctree.walkabout(visitor)

        return visitor.symbols


def esbonio_setup(server: EsbonioLanguageServer):
    document_symbols = DocumentSymbols(server)
    server.add_feature(document_symbols)
