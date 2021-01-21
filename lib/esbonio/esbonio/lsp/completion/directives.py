"""Logic around directive completions goes here."""
from __future__ import annotations

import importlib
import inspect
import re

from typing import Dict

from docutils.parsers.rst import Directive, directives
from pygls.types import CompletionItem, CompletionItemKind, InsertTextFormat
from sphinx.application import Sphinx

from esbonio.lsp.completion import CompletionHandler


def to_completion_item(name: str, directive) -> CompletionItem:
    """Convert an rst directive to its CompletionItem representation."""

    # 'Core' docutils directives are returned as tuples (modulename, ClassName)
    # so its up to us to resolve the reference
    if isinstance(directive, tuple):
        mod, cls = directive

        modulename = "docutils.parsers.rst.directives.{}".format(mod)
        module = importlib.import_module(modulename)
        directive = getattr(module, cls)

    documentation = inspect.getdoc(directive)

    # TODO: Give better names to arguments based on what they represent.
    args = " ".join(
        "${{{0}:arg{0}}}".format(i) for i in range(1, directive.required_arguments + 1)
    )
    snippet = " {}:: {}$0".format(name, args)

    return CompletionItem(
        name,
        kind=CompletionItemKind.Class,
        detail="directive",
        documentation=documentation,
        insert_text=snippet,
        insert_text_format=InsertTextFormat.Snippet,
    )


DIRECTIVE = re.compile(
    r"""
    ^\s*        # directives may be indented
    \.\.        # they start with an rst comment
    [ ]*        # followed by a space
    ([\w-]+)?$  # with an optional name

    """,
    re.VERBOSE,
)


class DirectiveHandler(CompletionHandler):
    """A completion handler for directives."""

    def __init__(self, app: Sphinx):

        std_directives = {}
        py_directives = {}

        # Find directives that have been registered directly with docutils.
        dirs = {**directives._directive_registry, **directives._directives}

        if app is not None:

            # Find directives that are held in a Sphinx domain.
            # TODO: Implement proper domain handling, will focus on std + python for now
            domains = app.registry.domains
            std_directives = domains["std"].directives
            py_directives = domains["py"].directives

        dirs = {**dirs, **std_directives, **py_directives}
        self.directives = {k: to_completion_item(k, v) for k, v in dirs.items()}

    def suggest(self, rst, match, line, doc):
        return list(self.directives.values())


def init(rst: RstLanguageServer):

    handler = DirectiveHandler(rst.app)

    rst.logger.debug("Discovered %s directives", len(handler.directives))
    rst.add_completion_handler(DIRECTIVE, handler)
