import logging
import typing
from typing import IO
from typing import List

from docutils import nodes
from docutils.core import Publisher
from docutils.io import NullOutput
from docutils.io import StringInput
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from docutils.readers.standalone import Reader
from docutils.utils import Reporter
from sphinx.config import Config
from sphinx.io import SphinxDummyWriter
from sphinx.util import get_filetype
from sphinx.util.docutils import CustomReSTDispatcher

from .. import types
from ..app import Database
from ..app import Sphinx
from ..util import as_json
from . import sphinx_logger

SYMBOLS_TABLE = Database.Table(
    "symbols",
    [
        Database.Column(name="uri", dtype="TEXT"),  # TODO: Replace with foreign key??
        Database.Column(name="id", dtype="INTEGER"),
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="kind", dtype="INTEGER"),
        Database.Column(name="detail", dtype="TEXT"),
        Database.Column(name="range", dtype="JSON"),
        Database.Column(name="parent_id", dtype="INTEGER"),
        Database.Column(name="order_id", dtype="INTEGER"),
    ],
)

# SymbolKinds see: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#symbolKind
ClassSymbol = 5
StringSymbol = 15


def init_db(app: Sphinx, config: Config):
    app.esbonio.db.ensure_table(SYMBOLS_TABLE)


def update_symbols(app: Sphinx, docname: str, source):
    """Update the symbols defined in the given file."""

    filename = app.env.doc2path(docname)
    filetype = get_filetype(app.config.source_suffix, filename)

    reader = LoggingDoctreeReader(sphinx_logger)
    parser = app.registry.create_source_parser(app, filetype)

    # Reuse the settings from Sphinx's publisher.
    sphinx_pub = app.registry.get_publisher(app, filetype)
    settings = sphinx_pub.settings

    with disable_roles_and_directives():
        publisher = Publisher(
            parser=parser,
            reader=reader,
            writer=SphinxDummyWriter(),
            source_class=StringInput,
            destination=NullOutput(),
        )
        publisher.settings = settings
        publisher.set_source(source="\n".join(source), source_path=filename)
        publisher.publish()
        document = publisher.document

    visitor = SymbolVisitor(document)
    document.walkabout(visitor)

    uri = str(types.Uri.for_file(app.env.doc2path(docname, base=True)).resolve())
    symbols = [(uri, *s) for s in visitor.symbols]

    app.esbonio.db.clear_table(SYMBOLS_TABLE, uri=uri)
    app.esbonio.db.insert_values(SYMBOLS_TABLE, symbols)


def setup(app: Sphinx):
    app.connect("config-inited", init_db)

    # We want this to happen very early so that we see the symbols as written in the
    # file - before any fancy extensions make their changes.
    #
    # The only handler with a higher priority (i.e. 0), should be the handler we use
    # to override the contents of the file so that we stay in sync with the language
    # client.
    app.connect("source-read", update_symbols, priority=1)

    # TODO: Sphinx 7.x+ support
    # app.connect("include-read")


class a_directive(nodes.Element, nodes.Inline):
    """Represents a directive."""


class a_role(nodes.Element):
    """Represents a role."""

    def astext(self):
        return self["text"]


def dummy_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    node = a_role()
    node.line = lineno

    match = types.RST_ROLE.match(rawtext)
    if match is None:
        node.attributes["text"] = rawtext
    else:
        node.attributes.update(match.groupdict())
        node.attributes["text"] = match.group(0)

    return [node], []


def run_dummy_directive(self):
    """This is a dummy implementation"""
    node = a_directive()
    node.line = self.lineno

    node.attributes["name"] = self.name
    node.attributes["options"] = self.options

    if len(self.arguments) > 0:
        node.attributes["argument"] = self.arguments[0]
    else:
        node.attributes["argument"] = None

    if self.content:
        # This is essentially what `nested_parse_with_titles` does in Sphinx.
        # But by passing the content_offset to state.nested_parse we ensure any line
        # numbers remain relative to the start of the current file.
        current_titles = self.state.memo.title_styles
        current_sections = self.state.memo.section_level
        self.state.memo.title_styles = []
        self.state.memo.section_level = 0
        try:
            self.state.nested_parse(
                self.content, self.content_offset, node, match_titles=1
            )
        finally:
            self.state.memo.title_styles = current_titles
            self.state.memo.section_level = current_sections

    return [node]


class disable_roles_and_directives(CustomReSTDispatcher):
    """Disables all roles and directives from being expanded.

    The ``CustomReSTDispactcher`` from Sphinx is *very* cool.  It provides a way to
    override the mechanism used to lookup roles and directives during parsing!

    It's perfect for temporarily replacing all role and directive implementations with
    dummy ones. Parsing an rst document with these dummy implementations gives us
    something equivalent to an abstract syntax tree.

    """

    def directive(self, directive_name, language_module, document):
        # We still have access to the original dispatch mechanism
        # This allows us to adapt our dummy directive to match the "shape" of the real
        # directive implementation!
        impl, _ = self.directive_func(directive_name, language_module, document)
        if impl is None:
            # Fallback to some sensible defaults.
            has_content = True
            option_spec = None
            required_arguments = 0
            optional_arguments = 1
            final_argument_whitespace = True
        else:
            # Mimic the "shape" of the real directive
            if impl.option_spec is None:
                option_spec = None
            else:
                option_spec = {o: directives.unchanged for o in impl.option_spec}

            # It probably doesn't make sense to copy these values, as often the user's
            # usage of a directive will be incorrect.
            required_arguments = 0  # impl.required_arguments
            has_content = True  # impl.has_content

            optional_arguments = 1
            final_argument_whitespace = True

        attrs = {
            "has_content": has_content,
            "option_spec": option_spec,
            "required_arguments": required_arguments,
            "optional_arguments": optional_arguments,
            "final_argument_whitespace": final_argument_whitespace,
            "run": run_dummy_directive,
        }
        return type("DummyDirective", (Directive,), attrs), []

    def role(self, role_name, language_module, lineno, reporter):
        return dummy_role, []


class SymbolVisitor(nodes.NodeVisitor):
    """Used to extract all the symbols from a document."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.symbols: List[types.Symbol] = []
        """Holds the symbols for the document"""

        self.parents: List[int] = []
        """Holds the ids of the current hierarchy."""

        self.order: List[int] = [0]
        """Holds the current position at each level of the hierarchy."""

    def push_symbol(self, name: str, kind: int, range_: types.Range, detail: str = ""):
        """Push another symbol onto the hierarchy.

        Parameters
        ----------
        name
           The name of the symbol

        kind
           The kind of symbol

        range_
           The range denoting where the symbol is in the document.

        detail
           Additional details about the symbol
        """
        symbol_id = len(self.symbols)
        parent_id = self.parents[-1] if len(self.parents) > 0 else None

        order_id = self.order[-1]
        self.order[-1] += 1

        self.parents.append(symbol_id)
        self.order.append(0)

        self.symbols.append(
            (symbol_id, name, kind, detail, as_json(range_), parent_id, order_id)
        )

    def pop_symbol(self):
        """Pop the current level of the hierarchy."""
        self.parents.pop()
        self.order.pop()

    def visit_section(self, node: nodes.Node) -> None:
        name = node.children[0].astext()
        line = (node.line or 1) - 1
        range_ = types.Range(
            start=types.Position(line=line, character=0),
            end=types.Position(line=line, character=len(name) - 1),
        )

        self.push_symbol(name, StringSymbol, range_)

    def depart_section(self, node: nodes.Node) -> None:
        self.pop_symbol()

    def visit_a_directive(self, node: a_directive):
        argument = node.attributes.get("argument", None)
        directive = node.attributes.get("name", "<<unknown>>")

        name = None
        detail = ""

        if argument is not None and len(argument) > 0:
            name = argument

        if directive is not None and len(directive) > 0:
            detail = directive

        if name is None:
            name = directive

        line = (node.line or 1) - 1
        range_ = types.Range(
            start=types.Position(line=line, character=0),
            end=types.Position(line=line, character=len(name) - 1),
        )

        self.push_symbol(name, ClassSymbol, range_, detail=detail)

    def depart_a_directive(self, node: nodes.Node):
        self.pop_symbol()

    # TODO: Enable symbols for roles
    #       However the reported line numbers can be inaccurate...
    def visit_a_role(self, node: nodes.Node) -> None: ...

    def depart_a_role(self, node: nodes.Node) -> None: ...

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


class LogStream:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def write(self, text: str):
        self.logger.debug(text)


class LogReporter(Reporter):
    """A docutils reporter that writes to the given logger."""

    def __init__(
        self,
        logger: logging.Logger,
        source: str,
        report_level: int,
        halt_level: int,
        debug: bool,
        error_handler: str,
    ) -> None:
        stream = typing.cast(IO, LogStream(logger))
        super().__init__(
            source, report_level, halt_level, stream, debug, error_handler=error_handler
        )  # type: ignore


class LoggingDoctreeReader(Reader):
    """A reader that replaces the default reporter with one that redirects."""

    def __init__(self, logger: logging.Logger, *args, **kwargs):
        self.logger = logger
        super().__init__(*args, **kwargs)

    def new_document(self) -> nodes.document:
        document = super().new_document()

        reporter = document.reporter
        document.reporter = LogReporter(
            self.logger,
            reporter.source,
            reporter.report_level,
            reporter.halt_level,
            reporter.debug_flag,
            reporter.error_handler,
        )

        return document
