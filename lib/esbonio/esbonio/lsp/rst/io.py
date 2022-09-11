import logging
import typing
from typing import IO
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type

import pygls.uris as uri
from docutils import nodes
from docutils.core import Publisher
from docutils.io import NullOutput
from docutils.io import StringInput
from docutils.parsers.rst import Directive
from docutils.parsers.rst import Parser
from docutils.parsers.rst import directives
from docutils.parsers.rst import roles
from docutils.readers.standalone import Reader
from docutils.utils import Reporter
from docutils.writers import Writer
from pygls.workspace import Document
from sphinx.environment import default_settings

from esbonio.lsp.util.patterns import DIRECTIVE
from esbonio.lsp.util.patterns import ROLE


class a_directive(nodes.Element, nodes.Inline):
    """Represents a directive."""


class a_role(nodes.Element):
    """Represents a role."""


def dummy_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    node = a_role()
    node.line = lineno

    match = ROLE.match(rawtext)
    if match is None:
        node.attributes["text"] = rawtext
    else:
        node.attributes.update(match.groupdict())
        node.attributes["text"] = match.group(0)

    return [node], []


class DummyDirective(Directive):
    has_content = True

    def run(self):
        node = a_directive()
        node.line = self.lineno
        parent = self.state.parent
        lines = self.block_text

        # substitution definitions require special handling
        if isinstance(parent, nodes.substitution_definition):
            lines = parent.rawsource

        text = lines.split("\n")[0]
        match = DIRECTIVE.match(text)
        if match:
            node.attributes.update(match.groupdict())
            node.attributes["text"] = match.group(0)
        else:
            self.state.reporter.warning(f"Unable to parse directive: '{text}'")
            node.attributes["text"] = text

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


class disable_roles_and_directives:
    """Disables all roles and directives from being expanded.

    The ``CustomReSTDispactcher`` from Sphinx is *very* cool.
    It provides a way to override the mechanism used to lookup roles and directives
    during parsing!

    It's perfect for temporarily replacing all role and directive implementations with
    dummy ones. Parsing an rst document with these dummy implementations effectively
    gives us something that could be called an abstract syntax tree.

    Unfortunately, it's only available in a relatively recent version of Sphinx (4.4)
    so we have to implement the same idea ourselves for now.
    """

    def __init__(self) -> None:
        self.directive_backup: Optional[Callable] = None
        self.role_backup: Optional[Callable] = None

    def __enter__(self) -> None:
        self.directive_backup = directives.directive
        self.role_backup = roles.role

        directives.directive = self.directive
        roles.role = self.role

    def __exit__(self, exc_type: Type[Exception], exc_value: Exception, traceback: Any):
        directives.directive = self.directive_backup  # type: ignore
        roles.role = self.role_backup  # type: ignore

        self.directive_backup = None
        self.role_backup = None

    def directive(self, directive_name, language_module, document):
        return DummyDirective, []

    def role(self, role_name, language_module, lineno, reporter):
        return dummy_role, []


class DummyWriter(Writer):
    """A writer that doesn't do anything."""

    def translate(self):
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


class InitialDoctreeReader(Reader):
    """A reader that replaces the default reporter with one compatible with esbonio's
    logging setup."""

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


def read_initial_doctree(
    document: Document, logger: logging.Logger
) -> Optional[nodes.document]:
    """Parse the given reStructuredText document into its "initial" doctree.

    An "initial" doctree can be thought of as the abstract syntax tree of a
    reStructuredText document. This method disables all role and directives
    from being executed, instead they are replaced with nodes that simply
    represent that they exist.

    Parameters
    ----------
    document
       The document containing the reStructuredText source.

    logger
       Logger to log debug info to.
    """

    parser = Parser()
    with disable_roles_and_directives():
        publisher = Publisher(
            reader=InitialDoctreeReader(logger),
            parser=parser,
            writer=DummyWriter(),
            source_class=StringInput,
            destination=NullOutput(),
        )
        publisher.process_programmatic_settings(None, default_settings, None)
        publisher.set_source(
            source=document.source, source_path=uri.to_fs_path(document.uri)
        )
        publisher.publish()

        return publisher.document
