"""Logic around directive completions goes here."""
import inspect
import re
from typing import List

from docutils.parsers.rst import Directive
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import InsertTextFormat
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import TextEdit

from esbonio.lsp import CompletionContext
from esbonio.lsp import LanguageFeature
from esbonio.lsp import RstLanguageServer


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


class ArgumentCompletion:
    """A completion provider for directive arguments."""

    def complete_arguments(self, context: CompletionContext) -> List[CompletionItem]:
        """Return a list of completion items representing valid targets for the given
        directive.

        Parameters
        ----------
        context:
           The completion context
        """
        return []


class Directives(LanguageFeature):
    """Directive support for the language server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._argument_providers: List[ArgumentCompletion] = []
        """A list of providers that give completion suggestions for directive
        arguments."""

    def add_argument_provider(self, provider: ArgumentCompletion) -> None:
        self._argument_providers.append(provider)

    completion_triggers = [DIRECTIVE, PARTIAL_DIRECTIVE, PARTIAL_DIRECTIVE_OPTION]

    def complete(self, context: CompletionContext) -> List[CompletionItem]:

        # Do not suggest completions within the middle of Python code.
        if context.location == "py":
            return []

        groups = context.match.groupdict()

        if "argument" in groups:
            return self.complete_arguments(context)

        if "domain" in groups:
            return self.complete_directives(context)

        return self.complete_options(context)

    def complete_arguments(self, context: CompletionContext) -> List[CompletionItem]:

        arguments = []

        for provide in self._argument_providers:
            arguments += provide.complete_arguments(context) or []

        return arguments

    def complete_directives(self, context: CompletionContext) -> List[CompletionItem]:

        domain = context.match.groupdict()["domain"] or ""
        items = []

        for name, directive in self.rst.get_directives().items():

            if not name.startswith(domain):
                continue

            item = self.directive_to_completion_item(name, directive, context)
            items.append(item)

        return items

    def complete_options(self, context: CompletionContext) -> List[CompletionItem]:

        groups = context.match.groupdict()

        self.logger.info("Suggesting options")
        self.logger.debug("Match groups: %s", groups)

        indent = groups["indent"]

        # Search backwards so that we can determine the context for our completion
        linum = context.position.line - 1
        line = context.doc.lines[linum]

        while linum >= 0 and line.startswith(indent):
            linum -= 1
            line = context.doc.lines[linum]

        # Only offer completions if we're within a directive's option block
        match = DIRECTIVE.match(line)

        self.logger.debug("Context line:  %s", line)
        self.logger.debug("Context match: %s", match)

        if not match:
            return []

        domain = match.group("domain") or ""
        name = f"{domain}{match.group('name')}"

        options = self.rst.get_directive_options(name)
        return self.options_to_completion_items(options)

    def directive_to_completion_item(
        self, name: str, directive: Directive, context: CompletionContext
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
        context:
           The completion context
        """
        position = context.position
        groups = context.match.groupdict()
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

    def options_to_completion_items(self, options) -> List[CompletionItem]:
        return [
            CompletionItem(
                label=opt,
                detail="option",
                kind=CompletionItemKind.Field,
                insert_text=f"{opt}: ",
            )
            for opt in options
        ]


def esbonio_setup(rst: RstLanguageServer):

    directives = Directives(rst)
    rst.add_feature(directives)
