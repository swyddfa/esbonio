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
from .feature import LanguageFeature
from .rst import RstLanguageServer

PARTIAL_ROLE = re.compile(
    r"""
    (^|.*[^\w:])          # roles cannot be preceeded by certain characters
    (?P<role>:            # roles start with the ':' character
    (?!:)                 # make sure the next character is not ':'
    (?P<domain>[\w]+:)?   # there may be a domain namespace
    (?P<name>[\w-]*))     # match the role name
    $                     # ensure pattern only matches incomplete roles
    """,
    re.MULTILINE | re.VERBOSE,
)
"""A regular expression that matches a partial role.

For example::

   :re

Used when generating auto complete suggestions.
"""


PARTIAL_PLAIN_TARGET = re.compile(
    r"""
    (^|.*[^\w:])            # roles cannot be preceeded by certain chars
    (?P<role>:              # roles start with the ':' character
    (?!:)                   # make sure the next character is not ':'
    ((?P<domain>[\w]+):)?   # there may be a domain namespace
    (?P<name>[\w-]*)        # followed by the role name
    :)                      # the role name ends with a ':'
    `                       # the target begins with a '`'
    (?P<target>[^<`]*)      # match "plain link" targets
    $
    """,
    re.MULTILINE | re.VERBOSE,
)
"""A regular expression that matches a partial "plain" role target.

For example::

   :ref:`som

Used when generating auto complete suggestions.
"""

PARTIAL_ALIASED_TARGET = re.compile(
    r"""
    (^|.*[^\w:])            # roles cannot be preceeded by certain chars
    (?P<role>:              # roles start with the ':' character
    (?!:)                   # make sure the next character is not ':'
    ((?P<domain>[\w]+):)?   # there may be a domain namespace
    (?P<name>[\w-]*)        # followed by the role name
    :)                      # the role name ends with a ':'
    `                       # the target begins with a '`'`
    .*<                     # the actual target name starts after a '<'
    (?P<target>[^`]*)       # match "aliased" targets
    $
    """,
    re.MULTILINE | re.VERBOSE,
)
"""A regular expression that matches an "aliased" role target.

For example::

   :ref:`More info <som

Used when generating auto complete suggestions.
"""

ROLE = re.compile(
    r"""
    (?P<role>:              # roles begin with a ':' character
    (?!:)                   # the next character cannot be a ':'
    ((?P<domain>[\w+]):)?   # roles may optionally include a domain
    (?P<name>[\w-]*):)      # and have a name
    `                       # the target starts with a '`'`
    ([^<`>]*?<)?            # there may be an alias for the target
    (?P<target>[^<`>]*)     # match the target itself
    >?                      # an aliased target would have a closing '>'
    `                       # the target ends with a '`'`
    """,
    re.MULTILINE | re.VERBOSE,
)
"""A regular expression that matches a complete role definition

For example::

   :ref:`some_target`
   :ref:`See More <some_target>`
   :c:func:`some_func`
   :c:func:`This Function <some_func>`

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

    def complete_targets(
        self, doc: Document, match: "re.Match", name: str, domain: Optional[str] = None
    ) -> List[CompletionItem]:
        """Return a list of completion items representing valid targets for the given
        role.

        Parameters
        ----------
        doc:
           The document containing the match
        match:
           The match object that triggered the completion
        name:
           The name of the role
        domain:
           The domain the role is part of, if applicable.
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

    completion_triggers = [PARTIAL_ROLE, PARTIAL_PLAIN_TARGET, PARTIAL_ALIASED_TARGET]
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

    def complete(
        self, match: "re.Match", doc: Document, position: Position
    ) -> List[CompletionItem]:
        indent = match.group(1)

        if "target" in match.groupdict():
            return self.complete_targets(doc, match, position)

        # If there's no indent, then this can only be a role defn
        if indent == "":
            return self.complete_roles(match, position)

        # Otherwise, search backwards until we find a blank line or an unindent
        # so that we can determine the appropriate context.
        linum = position.line - 1

        try:
            line = doc.lines[linum]
        except IndexError:
            return self.complete_roles(match, position)

        while linum >= 0 and line.startswith(indent):
            linum -= 1
            line = doc.lines[linum]

        # Unless we are within a directive's options block, we should offer role
        # suggestions
        if DIRECTIVE.match(line):
            return []

        return self.complete_roles(match, position)

    def complete_roles(
        self, match: "re.Match", position: Position
    ) -> List[CompletionItem]:

        domain = match.groupdict()["domain"] or ""
        items = []

        for name, role in self.rst.get_roles().items():

            if not name.startswith(domain):
                continue

            item = self.role_to_completion_item(name, role, match, position)
            items.append(item)

        return items

    def complete_targets(
        self, doc: Document, match: "re.Match", position: Position
    ) -> List[CompletionItem]:

        groups = match.groupdict()
        domain = groups["domain"] or None
        name = groups["name"]

        targets = []
        self.logger.debug(
            "Suggesting targets for %s:%s: %s", domain or ":", name, match.groupdict()
        )

        for provide in self._target_providers:
            targets += provide.complete_targets(doc, match, name, domain) or []

        return targets

    def role_to_completion_item(
        self, name: str, role, match: "re.Match", position: Position
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
        match:
           The regular expression match object that represents the line we are providing
           the autocomplete suggestions for.
        position:
           The position in the source code where the autocompletion request was sent
           from.
        """

        groups = match.groupdict()

        line = position.line
        start = position.character - len(groups["role"])
        end = position.character

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
