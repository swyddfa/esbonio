import asyncio
import json
from typing import Dict
from typing import List
from typing import Optional

from lsprotocol import types

from esbonio.server import EsbonioLanguageServer
from esbonio.server import LanguageFeature
from esbonio.server import Uri
from esbonio.server.features.project_manager import ProjectManager


class SphinxSymbols(LanguageFeature):
    """Add support for ``textDocument/documentSymbol`` requests"""

    def __init__(self, server: EsbonioLanguageServer, manager: ProjectManager):
        super().__init__(server)
        self.manager = manager

    async def document_symbol(
        self, params: types.DocumentSymbolParams
    ) -> Optional[List[types.DocumentSymbol]]:
        """Called when a document symbols request is received."""

        uri = Uri.parse(params.text_document.uri)
        if (project := self.manager.get_project(uri)) is None:
            return None

        symbols = await project.get_document_symbols(uri)
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

    async def workspace_symbol(
        self, params: types.WorkspaceSymbolParams
    ) -> Optional[List[types.WorkspaceSymbol]]:
        """Called when a workspace symbol request is received."""

        tasks = []
        for project in self.manager.projects.values():
            tasks.append(
                asyncio.create_task(project.get_workspace_symbols(params.query))
            )

        symbols = await asyncio.gather(*tasks)
        result: List[types.WorkspaceSymbol] = []

        for batch in symbols:
            for uri_str, name, kind, detail, range_json, container in batch:
                uri = Uri.parse(uri_str)
                range_ = self.converter.structure(json.loads(range_json), types.Range)

                if detail not in {"", name}:
                    display_name = f"{name} {detail}"
                else:
                    display_name = name

                result.append(
                    types.WorkspaceSymbol(
                        location=types.Location(uri=str(uri), range=range_),
                        name=display_name,
                        kind=self.converter.structure(kind, types.SymbolKind),
                        container_name=container,
                    )
                )

        return result


def esbonio_setup(server: EsbonioLanguageServer, project_manager: ProjectManager):
    symbols = SphinxSymbols(server, project_manager)
    server.add_feature(symbols)
