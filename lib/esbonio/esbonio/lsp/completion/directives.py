"""Logic around directive completions goes here."""
import importlib
import inspect
import re

from typing import List

from docutils.parsers.rst import directives
from pygls.types import CompletionItem, CompletionItemKind, InsertTextFormat

from esbonio.lsp import RstLanguageServer


def resolve_directive(directive):

    # 'Core' docutils directives are returned as tuples (modulename, ClassName)
    # so its up to us to resolve the reference
    if isinstance(directive, tuple):
        mod, cls = directive

        modulename = "docutils.parsers.rst.directives.{}".format(mod)
        module = importlib.import_module(modulename)
        directive = getattr(module, cls)

    return directive


def directive_to_completion_item(name: str, directive) -> CompletionItem:
    """Convert an rst directive to its CompletionItem representation."""

    directive = resolve_directive(directive)
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


def options_to_completion_items(directive) -> List[CompletionItem]:
    """Convert a directive's options to a list of completion items."""

    directive = resolve_directive(directive)
    options = directive.option_spec

    if options is None:
        return []

    return [
        CompletionItem(
            opt, detail="option", kind=CompletionItemKind.Field, insert_text=f"{opt}:"
        )
        for opt in options
    ]


class DirectiveCompletion:
    """A completion handler for directives."""

    def __init__(self, rst: RstLanguageServer):
        self.rst = rst

    def initialize(self):
        self.discover()

    def discover(self):
        std_directives = {}
        py_directives = {}

        # Find directives that have been registered directly with docutils.
        dirs = {**directives._directive_registry, **directives._directives}

        if self.rst.app is not None:

            # Find directives that are held in a Sphinx domain.
            # TODO: Implement proper domain handling, will focus on std + python for now
            domains = self.rst.app.registry.domains
            std_directives = domains["std"].directives
            py_directives = domains["py"].directives

        dirs = {**dirs, **std_directives, **py_directives}

        self.directives = {
            k: directive_to_completion_item(k, v)
            for k, v in dirs.items()
            if k != "restructuredtext-test-directive"
        }

        self.options = {
            k: options_to_completion_items(v)
            for k, v in dirs.items()
            if k in self.directives
        }

        self.rst.logger.debug("Discovered %s directives", len(self.directives))

    suggest_triggers = [
        re.compile(
            r"""
            ^\s*                # directives may be indented
            \.\.                # they start with an rst comment
            [ ]*                # followed by a space
            (?P<name>[\w-]+)?$  # with an optional name
            """,
            re.VERBOSE,
        ),
        re.compile(
            r"""
            (?P<indent>\s+)   # directive options must only be preceeded by whitespace
            :                 # they start with a ':'
            (?P<name>[\w-]*)  # they have a name
            $
            """,
            re.VERBOSE,
        ),
    ]

    def suggest(self, match, doc, position) -> List[CompletionItem]:
        groups = match.groupdict()

        if "indent" not in groups:
            return list(self.directives.values())

        # Search backwards so that we can determine the context for our completion
        indent = groups["indent"]
        linum = position.line - 1
        line = doc.lines[linum]

        while line.startswith(indent):
            linum -= 1
            line = doc.lines[linum]

        # Only offer completions if we're within a directive's option block
        match = re.match(r"\s*\.\.[ ]*(?P<name>[\w-]+)::", line)
        if not match:
            return []

        return self.options.get(match.group("name"), [])


def setup(rst: RstLanguageServer):

    directive_completion = DirectiveCompletion(rst)
    rst.add_feature(directive_completion)
