from typing import Optional

from docutils import nodes
from docutils.nodes import NodeVisitor
from pygls.lsp.types import DocumentSymbol
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import SymbolKind


class SymbolVisitor(NodeVisitor):
    """A visitor used to build the hierarchy we return from a
    ``textDocument/documentSymbol`` request.

    """

    def __init__(self, rst, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = rst.logger
        self.symbols = []
        self.symbol_stack = []

    @property
    def current_symbol(self) -> Optional[DocumentSymbol]:

        if len(self.symbol_stack) == 0:
            return None

        return self.symbol_stack[-1]

    def push_symbol(self):
        symbol = DocumentSymbol(
            name="",
            kind=SymbolKind.String,
            range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=10),
            ),
            selection_range=Range(
                start=Position(line=1, character=0),
                end=Position(line=1, character=10),
            ),
            children=[],
        )
        current_symbol = self.current_symbol

        if not current_symbol:
            self.symbols.append(symbol)
        else:
            if current_symbol.children is None:
                current_symbol.children = [symbol]
            else:
                current_symbol.children.append(symbol)

        self.symbol_stack.append(symbol)
        return symbol

    def pop_symbol(self):
        self.symbol_stack.pop()

    def visit_section(self, node: nodes.Node) -> None:
        self.push_symbol()

    def depart_section(self, node: nodes.Node) -> None:
        self.pop_symbol()

    def visit_title(self, node: nodes.Node) -> None:

        symbol = self.current_symbol
        has_parent = True

        if symbol is None:
            has_parent = False
            symbol = self.push_symbol()

        name = node.astext()
        line = (node.line or 1) - 1

        symbol.name = name
        symbol.range.start.line = line
        symbol.range.end.line = line
        symbol.range.end.character = len(name) - 1
        symbol.selection_range.start.line = line
        symbol.selection_range.end.line = line
        symbol.selection_range.end.character = len(name) - 1

        if not has_parent:
            self.pop_symbol()

    def depart_title(self, node: nodes.Node) -> None:
        pass

    def visit_a_directive(self, node: nodes.Element):
        symbol = self.push_symbol()

        name = node["text"]  # type: ignore
        line = (node.line or 1) - 1

        symbol.name = name
        symbol.kind = SymbolKind.Class
        symbol.range.start.line = line
        symbol.range.end.line = line
        symbol.range.end.character = len(name) - 1
        symbol.selection_range.start.line = line
        symbol.selection_range.end.line = line
        symbol.selection_range.end.character = len(name) - 1

    def depart_a_directive(self, node: nodes.Node):
        self.pop_symbol()

    # TODO: Enable symbols for roles
    #       However the reported line numbers can be inaccurate...
    def visit_a_role(self, node: nodes.Node) -> None:
        ...

    def depart_a_role(self, node: nodes.Node) -> None:
        ...

    # TODO: Enable symbols for definition list items
    #       However the reported line numbers appear to be inaccurate...

    def visit_Text(self, node: nodes.Node) -> None:
        pass

    def depart_Text(self, node: nodes.Node) -> None:
        pass

    def unknown_visit(self, node: nodes.Node) -> None:
        pass

    def unknown_departure(self, node: nodes.Node) -> None:
        pass
