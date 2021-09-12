"""Logic around directive completions goes here."""
import inspect
import re
from typing import List
from typing import Optional

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
    (\s*)                           # directives can be indented
    (?P<directive>
      \.\.                          # directives start with a comment
      [ ]?                          # followed by a space
      ((?P<domain>[\w]+):(?!:))?    # directives may include a domain
      (?P<name>[\w-]+)?             # directives have a name
      (::)?                         # directives end with '::'
    )
    ([\s]+(?P<argument>.*$))?       # directives may take an argument
    """,
    re.VERBOSE,
)
"""A regular expression to detect and parse partial and complete directives.

This does **not** include any options or content that may be included underneath
the initial declaration. The language server breaks a directive down into a number
of parts::

                   vvvvvv argument
   .. c:function:: malloc
   ^^^^^^^^^^^^^^^ directive
        ^^^^^^^^ name
      ^ domain (optional)
"""


DIRECTIVE_OPTION = re.compile(
    r"""
    (?P<indent>\s+)       # directive options must be indented
    (?P<option>
      :                   # options start with a ':'
      (?P<name>[\w-]+)?   # options have a name
      :?                  # options end with a ':'
    )
    (\s*
      (?P<value>.*)       # options can have a value
    )?
    """,
    re.VERBOSE,
)
"""A regular expression used to detect and parse partial and complete directive options.

The language server breaks an option down into a number of parts::

               vvvvvv value
   |   :align: center
       ^^^^^^^ option
        ^^^^^ name
    ^^^ indent
"""


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

    completion_triggers = [DIRECTIVE, DIRECTIVE_OPTION]

    def complete(self, context: CompletionContext) -> List[CompletionItem]:

        # Do not suggest completions within the middle of Python code.
        if context.location == "py":
            return []

        groups = context.match.groupdict()

        # Are we completing a directive's options?
        if "directive" not in groups:
            return self.complete_options(context)

        # Are we completing the directive's argument?
        directive_end = context.match.span()[0] + len(groups["directive"])
        complete_directive = groups["directive"].endswith("::")

        if complete_directive and directive_end < context.position.character:
            return self.complete_arguments(context)

        return self.complete_directives(context)

    def complete_arguments(self, context: CompletionContext) -> List[CompletionItem]:
        self.logger.debug("Completing arguments")
        arguments = []

        for provide in self._argument_providers:
            arguments += provide.complete_arguments(context) or []

        return arguments

    def complete_directives(self, context: CompletionContext) -> List[CompletionItem]:
        self.logger.debug("Completing directives")

        items = []
        match = context.match
        groups = match.groupdict()

        domain = ""
        if groups["domain"]:
            domain = f'{groups["domain"]}:'

        # Calculate the range of text the CompletionItems should edit.
        # If there is an existing argument to the directive, we should leave it untouched
        # otherwise, edit the whole line to insert any required arguments.
        start = match.span()[0] + match.group(0).find(".")
        include_argument = True
        end = match.span()[1]

        if groups["argument"]:
            include_argument = False
            end = match.span()[0] + match.group(0).find("::") + 2

        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )

        for name, directive in self.rst.get_directives().items():

            if not name.startswith(domain):
                continue

            item = self.directive_to_completion_item(
                name, directive, context, include_argument=include_argument
            )
            item.text_edit = TextEdit(range=range_, new_text=item.insert_text)
            item.insert_text = None

            items.append(item)

        return items

    def complete_options(self, context: CompletionContext) -> List[CompletionItem]:

        directive = self.get_directive_context(context)
        if not directive:
            return []

        self.logger.debug("Completing options")

        domain = ""
        if directive.group("domain"):
            domain = f'{directive.group("domain")}:'

        name = f"{domain}{directive.group('name')}"

        items = []
        match = context.match
        groups = match.groupdict()

        option = groups["option"]
        start = match.span()[0] + match.group(0).find(option)
        end = start + len(option)

        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )

        for option in self.rst.get_directive_options(name):
            item = self.option_to_completion_item(option)
            item.text_edit = TextEdit(range=range_, new_text=item.insert_text)
            item.insert_text = None

            items.append(item)

        self.logger.debug(items)
        return items

    def get_directive_context(self, context: CompletionContext) -> Optional["re.Match"]:
        """Used to determine which directive we should be offering completions for.

        When suggestions should be generated this returns an :class:`python:re.Match`
        object representing the directive the options are associated with. In the
        case where suggestions should not be generated this will return ``None``

        Parameters
        ----------
        context:
          The completion context
        """

        match = context.match
        groups = match.groupdict()
        indent = groups["indent"]

        self.logger.debug("Match groups: %s", groups)

        # Search backwards so that we can determine the context for our completion
        linum = context.position.line - 1
        line = context.doc.lines[linum]

        while linum >= 0 and line.startswith(indent):
            linum -= 1
            line = context.doc.lines[linum]

        # Only offer completions if we're within a directive's option block
        directive = DIRECTIVE.match(line)
        self.logger.debug("Context line:  %s", line)
        self.logger.debug("Context match: %s", directive)

        if not directive:
            return None

        # Now that we know we're in a directive's option block, is the completion
        # request coming from a valid position on the line?
        option = groups["option"]
        start = match.span()[0] + match.group(0).find(option)
        end = start + len(option) + 1

        if start <= context.position.character <= end:
            return directive

        return None

    def directive_to_completion_item(
        self,
        name: str,
        directive: Directive,
        context: CompletionContext,
        include_argument: bool = True,
    ) -> CompletionItem:
        """Convert an rst directive to its CompletionItem representation.

        Parameters
        ----------
        name:
           The name of the directive as a user would type in an reStructuredText
           document
        directive:
           The class definition that implements the Directive's behavior
        context:
           The completion context
        include_argument:
           A flag that indicates if a placholder for any directive arguments should
           be included
        """
        args = ""
        documentation = inspect.getdoc(directive)
        insert_format = InsertTextFormat.PlainText

        # Ignore directives that do not provide their own documentation.
        if any(
            [
                documentation.startswith("Base class for reStructuredText directives."),
                documentation.startswith("A base class for Sphinx directives."),
            ]
        ):
            documentation = None

        # TODO: Give better names to arguments based on what they represent.
        if include_argument:
            insert_format = InsertTextFormat.Snippet
            args = " " + " ".join(
                "${{{0}:arg{0}}}".format(i)
                for i in range(1, directive.required_arguments + 1)
            )

        insert_text = f".. {name}::{args}"

        return CompletionItem(
            label=name,
            kind=CompletionItemKind.Class,
            detail="directive",
            documentation=documentation,
            filter_text=insert_text,
            insert_text=insert_text,
            insert_text_format=insert_format,
        )

    def option_to_completion_item(self, option: str) -> CompletionItem:
        """Convert an directive option to its CompletionItem representation.

        Parameters
        ----------
        option:
           The option's name
        """
        insert_text = f":{option}:"

        return CompletionItem(
            label=option,
            detail="option",
            kind=CompletionItemKind.Field,
            filter_text=insert_text,
            insert_text=insert_text,
        )


def esbonio_setup(rst: RstLanguageServer):

    directives = Directives(rst)
    rst.add_feature(directives)
