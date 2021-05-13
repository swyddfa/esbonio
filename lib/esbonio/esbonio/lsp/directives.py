"""Logic around directive completions goes here."""
import importlib
import inspect
import re

from typing import List, Union, Tuple

from docutils.parsers.rst import directives, Directive
from pygls.lsp.types import (
    CompletionItem,
    CompletionItemKind,
    InsertTextFormat,
    Position,
    Range,
    TextEdit,
)
from pygls.workspace import Document

import esbonio.lsp as lsp
from esbonio.lsp.sphinx import get_domains


DIRECTIVE = re.compile(
    r"""
    (?P<indent>\s*)             # directives can be indented
    (?P<directive>\.\.          # start with a comment
    [ ]                         # separated by a space
    (?P<domain>[\w]+:)?         # with an optional domain namespace
    (?P<name>[\w-]+))           # with a name
    ::
    ([\s]+(?P<argument>.*$))?   # some directives may take an argument
    """,
    re.VERBOSE,
)
"""A regular expression that matches a complete, valid directive declaration. Not
including any options or content."""


PARTIAL_DIRECTIVE = re.compile(
    r"""
    (?P<indent>^\s*)          # directives can be indented
    \.\.                      # start with a commment
    (?P<prefix>[ ]?)          # may have a space
    (?P<domain>[\w]+:)?       # with an optional domain namespace
    (?P<name>[\w-]+)?         # with an optional name
    $
    """,
    re.VERBOSE,
)
"""A regular expression that matches a partial directive declaraiton. Used when
generating auto complete suggestions."""


PARTIAL_DIRECTIVE_OPTION = re.compile(
    r"""
    (?P<indent>\s+)   # directive options must only be preceeded by whitespace
    :                 # they start with a ':'
    (?P<name>[\w-]*)  # they have a name
    $
    """,
    re.VERBOSE,
)
"""A regular expression that matches a partial directive option. Used when generating
auto complete suggestions."""


class Directives(lsp.LanguageFeature):
    """Directive support for the language server."""

    def initialized(self, config: lsp.SphinxConfig):
        self.discover()

    def discover(self):
        """Build an index of all available directives and the their options."""
        ignored_directives = ["restructuredtext-test-directive"]

        # Find directives that have been registered directly with docutils.
        found_directives = {**directives._directive_registry, **directives._directives}

        # Find directives under Sphinx domains
        for prefix, domain in get_domains(self.rst.app):
            fmt = "{prefix}:{name}" if prefix else "{name}"

            for name, directive in domain.directives.items():
                key = fmt.format(name=name, prefix=prefix)
                found_directives[key] = directive

        self.directives = {
            k: self.resolve_directive(v)
            for k, v in found_directives.items()
            if k not in ignored_directives
        }

        self.options = {
            k: self.options_to_completion_items(k, v)
            for k, v in self.directives.items()
        }

        self.logger.info("Discovered %s directives", len(self.directives))
        self.logger.debug("Directives: %s", list(self.directives.keys()))

    def resolve_directive(self, directive: Union[Directive, Tuple[str]]):

        # 'Core' docutils directives are returned as tuples (modulename, ClassName)
        # so its up to us to resolve the reference
        if isinstance(directive, tuple):
            mod, cls = directive

            modulename = "docutils.parsers.rst.directives.{}".format(mod)
            module = importlib.import_module(modulename)
            directive = getattr(module, cls)

        return directive

    suggest_triggers = [PARTIAL_DIRECTIVE, PARTIAL_DIRECTIVE_OPTION]
    """Regular expressions that match lines that we want to offer autocomplete
    suggestions for."""

    def suggest(
        self, match: "re.Match", doc: Document, position: Position
    ) -> List[CompletionItem]:
        self.logger.debug("Trigger match: %s", match)
        groups = match.groupdict()

        if "domain" in groups:
            return self.suggest_directives(match, position)

        return self.suggest_options(match, doc, position)

    def suggest_directives(self, match, position) -> List[CompletionItem]:
        self.logger.debug("Suggesting directives")

        domain = match.groupdict()["domain"] or ""
        items = []

        for name, directive in self.directives.items():

            if not name.startswith(domain):
                continue

            item = self.directive_to_completion_item(name, directive, match, position)
            items.append(item)

        return items

    def suggest_options(
        self, match: "re.Match", doc: Document, position: Position
    ) -> List[CompletionItem]:

        groups = match.groupdict()

        self.logger.info("Suggesting options")
        self.logger.debug("Match groups: %s", groups)

        indent = groups["indent"]

        # Search backwards so that we can determine the context for our completion
        linum = position.line - 1
        line = doc.lines[linum]

        while line.startswith(indent):
            linum -= 1
            line = doc.lines[linum]

        # Only offer completions if we're within a directive's option block
        match = DIRECTIVE.match(line)

        self.logger.debug("Context line:  %s", line)
        self.logger.debug("Context match: %s", match)

        if not match:
            return []

        domain = match.group("domain") or ""
        name = f"{domain}{match.group('name')}"

        return self.options.get(name, [])

    def directive_to_completion_item(
        self, name: str, directive: Directive, match: "re.Match", position: Position
    ) -> CompletionItem:
        """Convert an rst directive to its CompletionItem representation.

        Previously, it was fine to pre-convert directives into their completion item
        representation during the :meth:`discover` phase. However a number of factors
        combined to force this to be something we have to compute specifically for each
        completion site.

        It all stems from directives that live under a namespaced domain e.g.
        ``.. c:macro::``. First in order to get trigger character completions for
        directives, we need to allow users to start typing the directive name
        immediately after the second dot and have the CompletionItem insert the leading
        space. Which is exactly what we used to do, setting
        ``insert_text=" directive::"`` and we were done.

        However with domain support, we introduced the possibility of a ``:`` character
        in the name of a directive. You can imagine a scenario where a user types in a
        domain namespace, say ``py:`` in order to filter down the list of options to
        directives that belong to that namespace. With ``:`` being a trigger character
        for role completions and the like, this would cause editors like VSCode to issue
        a new completion request ignoring the old one.

        That isn't necessarily the end of the world, but with CompletionItems assuming
        that they were following the ``..`` characters, the ``insert_text`` was no
        longer correct leading to broken completions like ``..py: py:function::``.

        In order to handle the two scenarios, conceptually the easiest approach is to
        switch to using a ``text_edit`` and replace the entire line with the correct
        text. Unfortunately in practice this was rather fiddly.

        Upon first setting the ``text_edit`` field VSCode suddenly stopped presenting
        any options! After much debugging, head scratching and searching, I eventually
        found a `couple <https://github.com/microsoft/vscode/issues/38982>`_ of
        `issues <https://github.com/microsoft/vscode/issues/41208>`_ that hinted as to
        what was happening.

        I **think** what happens is that since the ``range`` of the text edit extends
        back to the start of the line VSCode considers the entire line to be the filter
        for the CompletionItems so it's looking to select items that start with ``..``
        - which is none of them!

        To work around this, we additionaly need to set the ``filter_text`` field so
        that VSCode computes matches against that instead of the label. Then in order
        for the items to be shown the value of that field needs to be ``..my:directive``
        so it corresponds with what the user has actually written.

        Parameters
        ----------
        name:
           The name of the directive as a user would type in an reStructuredText
           document
        directive:
           The class definition that implements the Directive's behavior
        match:
           The regular expression match object that represents the line we are providing
           the autocomplete suggestions for.
        position:
           The position in the source code where the autocompletion request was sent
           from.
        """
        groups = match.groupdict()
        prefix = groups["prefix"]
        indent = groups["indent"]

        documentation = inspect.getdoc(directive)

        # Ignore directives that do not provide their own documentation.
        if any(
            [
                documentation.startswith("Base class for reStructuredText directives."),
                documentation.startswith("A base class for Sphinx directives."),
            ]
        ):
            documentation = None

        # TODO: Give better names to arguments based on what they represent.
        args = " ".join(
            "${{{0}:arg{0}}}".format(i)
            for i in range(1, directive.required_arguments + 1)
        )

        return CompletionItem(
            label=name,
            kind=CompletionItemKind.Class,
            detail="directive",
            documentation=documentation,
            filter_text=f"..{prefix}{name}",
            insert_text_format=InsertTextFormat.Snippet,
            text_edit=TextEdit(
                range=Range(
                    start=Position(line=position.line, character=0),
                    end=Position(line=position.line, character=position.character - 1),
                ),
                new_text=f"{indent}.. {name}:: {args}",
            ),
        )

    def options_to_completion_items(
        self, name: str, directive: Directive
    ) -> List[CompletionItem]:
        """Convert a directive's options to a list of completion items.

        Unfortunately, the ``autoxxx`` family of directives are a little different.
        Each ``autoxxxx`` directive name resolves to the same ``AutodocDirective`` class.
        That paricular directive does not have any options, instead the options are
        held on the particular Documenter that documents that object type.

        This method does the lookup in order to determine what those options are.

        Parameters
        ----------
        name:
           The name of the directive as it appears in an rst file.
        directive:
           The directive whose options we are creating completions for.
        """

        options = directive.option_spec

        # autoxxx directives require special handlng.
        if name.startswith("auto") and self.rst.app:
            self.logger.debug("Processing options for '%s' directive", name)
            name = name.replace("auto", "")

            self.logger.debug("Documenter name is '%s'", name)
            documenter = self.rst.app.registry.documenters.get(name, None)

            if documenter is not None:
                options = documenter.option_spec

        if options is None:
            return []

        return [
            CompletionItem(
                label=opt,
                detail="option",
                kind=CompletionItemKind.Field,
                insert_text=f"{opt}: ",
            )
            for opt in options
        ]


def setup(rst: lsp.RstLanguageServer):

    directive_completion = Directives(rst)
    rst.add_feature(directive_completion)
