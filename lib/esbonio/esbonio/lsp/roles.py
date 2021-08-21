"""Role support."""
import re
from typing import List
from typing import Optional

from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import TextEdit
from pygls.workspace import Document

from .directives import DIRECTIVE
from .feature import CompletionContext
from .feature import LanguageFeature
from .rst import RstLanguageServer

ROLE = re.compile(
    r"""
    (?P<role>
      ([^\w:]|^)                       # roles cannot be preceeded by letter chars
      :                               # roles begin with a ':' character
      (?!:)                           # the next character cannot be a ':'
      ((?P<domain>[\w]+):(?=\w))?     # roles may include a domain (that must be followed by a word character)
      ((?P<name>[\w-]+):?)?           # roles have a name
    )
    (?P<target>
      `                               # targets begin with a '`' character
      ((?P<alias>[^<`>]*?)<)?         # targets may specify an alias
      (?P<label>[^<`>]*)?             # targets contain a label
      >?                              # labels end with a '>' when there's an alias
      `?                              # targets end with a '`' character
    )?
    """,
    re.VERBOSE,
)
"""A regular expression to detect and parse parial and complete roles.

See :func:`tests.test_roles.test_role_regex` for a list of example strings this pattern
matches.
"""


class TargetDefinition:
    """A definition provider for role targets"""

    def find_definitions(
        self, doc: Document, match: "re.Match", name: str, domain: Optional[str] = None
    ) -> List[Location]:
        """Return a list of locations representing the definition of the given role
        target.

        Parameters
        ----------
        doc:
           The document containing the match
        match:
           The match object that triggered the definition request
        name:
           The name of the role
        domain:
           The domain the role is part of, if applicable.
        """
        return []


class TargetCompletion:
    """A completion provider for role targets"""

    def complete_targets(self, context: CompletionContext) -> List[CompletionItem]:
        """Return a list of completion items representing valid targets for the given
        role.

        Parameters
        ----------
        context:
           The completion context
        """
        return []


class Roles(LanguageFeature):
    """Role support for the language server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._definition_providers: List[TargetDefinition] = []
        """A list of providers that locate the definition for the given role target."""

        self._target_providers: List[TargetCompletion] = []
        """A list of providers that give completion suggestions for role target
        objects."""

    def add_definition_provider(self, provider: TargetDefinition) -> None:
        self._definition_providers.append(provider)

    def add_target_provider(self, provider: TargetCompletion) -> None:
        self._target_providers.append(provider)

    completion_triggers = [ROLE]
    definition_triggers = [ROLE]

    def definition(
        self, match: "re.Match", doc: Document, pos: Position
    ) -> List[Location]:

        groups = match.groupdict()
        domain = groups["domain"] or None
        name = groups["name"]

        definitions = []
        self.logger.debug(
            "Suggesting definitions for %s%s: %s",
            domain or ":",
            name,
            match.groupdict(),
        )

        for provide in self._definition_providers:
            definitions += provide.find_definitions(doc, match, name, domain) or []

        return definitions

    def complete(self, context: CompletionContext) -> List[CompletionItem]:

        # Do not suggest completions within the middle of Python code.
        if context.location == "py":
            return []

        groups = context.match.groupdict()
        if groups["target"]:
            return self.complete_targets(context)

        # If there's no indent, then this can only be a role defn
        indent = context.match.group(1)
        if indent == "":
            return self.complete_roles(context)

        # Otherwise, search backwards until we find a blank line or an unindent
        # so that we can determine the appropriate context.
        linum = context.position.line - 1

        try:
            line = context.doc.lines[linum]
        except IndexError:
            return self.complete_roles(context)

        while linum >= 0 and line.startswith(indent):
            linum -= 1
            line = context.doc.lines[linum]

        # Unless we are within a directive's options block, we should offer role
        # suggestions
        if DIRECTIVE.match(line):
            return []

        return self.complete_roles(context)

    def complete_roles(self, context: CompletionContext) -> List[CompletionItem]:

        domain = context.match.groupdict()["domain"] or ""
        items = []

        for name, role in self.rst.get_roles().items():

            if not name.startswith(domain):
                continue

            item = self.role_to_completion_item(name, role, context)
            items.append(item)

        return items

    def complete_targets(self, context: CompletionContext) -> List[CompletionItem]:
        """Generate the list of role target completion suggestions."""

        targets = []

        groups = context.match.groupdict()
        startchar = "<" if "<" in groups["target"] else "`"
        endchars = ">`" if "<" in groups["target"] else "`"

        start, end = context.match.span()
        start += context.match.group(0).index(startchar) + 1
        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )
        prefix = context.match.group(0)[start:]

        for provide in self._target_providers:
            candidates = provide.complete_targets(context) or []

            for candidate in candidates:

                # Don't interfere with items that already carry a `text_edit`, allowing
                # some providers (like intersphinx) to do something special.
                if not candidate.text_edit:
                    new_text = candidate.insert_text or candidate.label

                    # This is rather annoying, but `filter_text` needs to start with
                    # the text we are going to replace, otherwise VSCode won't show our
                    # suggestions!
                    candidate.filter_text = f"{prefix}{new_text}"

                    candidate.text_edit = TextEdit(range=range_, new_text=new_text)
                    candidate.insert_text = None

                if not candidate.text_edit.new_text.endswith(endchars):
                    candidate.text_edit.new_text += endchars

                targets.append(candidate)

        return targets

    def role_to_completion_item(
        self, name: str, role, context: CompletionContext
    ) -> CompletionItem:
        """Convert an rst role to its CompletionItem representation.

        With domain support it's necessary to compute the CompletionItem representation
        specifically for each completion site. See
        :meth:`~esbonio.lsp.directives.Directives.directive_to_completion_item` for
        more historical information.

        For some reason, even though these completion items are constructed in the same
        manner as the ones for directives using them in VSCode does not feel as nice....

        Parameters
        ----------
        name:
           The name of the role as a user would type into an reStructuredText document.
        role:
           The implementation of the role.
        context:
           The completion context
        """

        groups = context.match.groupdict()

        line = context.position.line
        start = context.position.character - len(groups["role"])
        end = context.position.character

        insert_text = f":{name}:"

        item = CompletionItem(
            label=name,
            kind=CompletionItemKind.Function,
            filter_text=insert_text,
            detail="role",
            text_edit=TextEdit(
                range=Range(
                    start=Position(line=line, character=start),
                    end=Position(line=line, character=end),
                ),
                new_text=insert_text,
            ),
        )

        return item


def esbonio_setup(rst: RstLanguageServer):
    roles = Roles(rst)
    rst.add_feature(roles)
