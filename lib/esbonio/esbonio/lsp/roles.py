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
from .rst import CompletionContext
from .rst import LanguageFeature
from .rst import RstLanguageServer

ROLE = re.compile(
    r"""
    ([^\w:]|^\s*)                     # roles cannot be preceeded by letter chars
    (?P<role>
      :                               # roles begin with a ':' character
      (?!:)                           # the next character cannot be a ':'
      ((?P<domain>[\w]+):(?=\w))?     # roles may include a domain (that must be followed by a word character)
      ((?P<name>[\w-]+):?)?           # roles have a name
    )
    (?P<target>
      `                               # targets begin with a '`' character
      ((?P<alias>[^<`>]*?)<)?         # targets may specify an alias
      (?P<modifier>[!~])?             # targets may have a modifier
      (?P<label>[^<`>]*)?             # targets contain a label
      >?                              # labels end with a '>' when there's an alias
      `?                              # targets end with a '`' character
    )?
    """,
    re.VERBOSE,
)
"""A regular expression to detect and parse parial and complete roles.

I'm not sure if there are offical names for the components of a role, but the
language server breaks a role down into a number of parts::

                 vvvvvv label
                v modifier(optional)
               vvvvvvvv target
   :c:function:`!malloc`
   ^^^^^^^^^^^^ role
      ^^^^^^^^ name
    ^ domain (optional)

The language server sometimes refers to the above as a "plain" role, in that the
role's target contains just the label of the object it is linking to. However it's
also possible to define "aliased" roles, where the link text in the final document
is overriden, for example::

                vvvvvvvvvvvvvvvvvvvvvvvv alias
                                          vvvvvv label
                                         v modifier (optional)
               vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv target
   :c:function:`used to allocate memory <~malloc>`
   ^^^^^^^^^^^^ role
      ^^^^^^^^ name
    ^ domain (optional)

See :func:`tests.test_roles.test_role_regex` for a list of example strings this pattern
is expected to match.
"""


DEFAULT_ROLE = re.compile(
    r"""
    (?<![:`])
    (?P<target>
      `                               # targets begin with a '`' character
      ((?P<alias>[^<`>]*?)<)?         # targets may specify an alias
      (?P<modifier>[!~])?             # targets may have a modifier
      (?P<label>[^<`>]*)?             # targets contain a label
      >?                              # labels end with a '>' when there's an alias
      `?                              # targets end with a '`' character
    )
    """,
    re.VERBOSE,
)
"""A regular expression to detect and parse parial and complete "default" roles.

A "default" role is the target part of a normal role - but without the ``:name:`` part.
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
        self, context: CompletionContext, domain: str, name: str
    ) -> List[CompletionItem]:
        """Return a list of completion items representing valid targets for the given
        role.

        Parameters
        ----------
        context:
           The completion context
        domain:
           The name of the domain the role is a member of
        name:
           The name of the role to generate completion suggestions for.
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

    completion_triggers = [ROLE, DEFAULT_ROLE]
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
        """Generate completion suggestions relevant to the current context.

        This function is a little intense, but its sole purpose is to determine the
        context in which the completion request is being made and either return
        nothing, or the results of :meth:`~esbonio.lsp.roles.Roles.complete_roles` or
        :meth:`esbonio.lsp.roles.Roles.complete_targets` whichever is appropriate.

        Parameters
        ----------
        context:
           The context of the completion request.
        """

        # Do not suggest completions within the middle of Python code.
        if context.location == "py":
            return []

        groups = context.match.groupdict()
        target = groups["target"]

        # All text matched by the regex
        text = context.match.group(0)
        start, end = context.match.span()

        if target:
            target_index = start + text.find(target)

            # Only trigger target completions if the request was made from within
            # the target part of the role.
            if target_index <= context.position.character <= end:
                return self.complete_targets(context)

        # If there's no indent, then this can only be a role definition
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

        match = context.match
        groups = match.groupdict()
        domain = groups["domain"] or ""
        items = []

        # Insert text starting from the starting ':' character of the role.
        start = match.span()[0] + match.group(0).find(":")
        end = start + len(groups["role"])

        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )

        for name, role in self.rst.get_roles().items():

            if not name.startswith(domain):
                continue

            item = self.role_to_completion_item(name, role, context)
            item.text_edit = TextEdit(range=range_, new_text=item.insert_text)
            item.insert_text = None

            items.append(item)

        return items

    def complete_targets(self, context: CompletionContext) -> List[CompletionItem]:
        """Generate the list of role target completion suggestions."""

        groups = context.match.groupdict()

        # Handle the default role case.
        if "role" not in groups:
            domain, name = self.rst.get_default_role()
            if not name:
                return []
        else:
            name = groups["name"]
            domain = groups["domain"] or ""

        # Only generate suggestions for "aliased" targets if the request comes from
        # within the <> chars.
        if groups["alias"]:
            text = context.match.group(0)
            start = context.match.span()[0] + text.find(groups["alias"])
            end = start + len(groups["alias"])

            if start <= context.position.character <= end:
                return []

        targets = []

        startchar = "<" if "<" in groups["target"] else "`"
        endchars = ">`" if "<" in groups["target"] else "`"

        start, end = context.match.span()
        start += context.match.group(0).index(startchar) + 1
        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )
        prefix = context.match.group(0)[start:]
        modifier = groups["modifier"] or ""

        for provide in self._target_providers:
            candidates = provide.complete_targets(context, domain, name) or []

            for candidate in candidates:

                # Don't interfere with items that already carry a `text_edit`, allowing
                # some providers (like filepaths) to do something special.
                if not candidate.text_edit:
                    new_text = candidate.insert_text or candidate.label

                    # This is rather annoying, but `filter_text` needs to start with
                    # the text we are going to replace, otherwise VSCode won't show our
                    # suggestions!
                    candidate.filter_text = f"{prefix}{new_text}"

                    candidate.text_edit = TextEdit(
                        range=range_, new_text=f"{modifier}{new_text}"
                    )
                    candidate.insert_text = None

                if not candidate.text_edit.new_text.endswith(endchars):
                    candidate.text_edit.new_text += endchars

                targets.append(candidate)

        return targets

    def role_to_completion_item(
        self, name: str, role, context: CompletionContext
    ) -> CompletionItem:
        """Convert an rst role to its CompletionItem representation.

        Parameters
        ----------
        name:
           The name of the role as a user would type into an reStructuredText document.
        role:
           The implementation of the role.
        context:
           The completion context
        """

        insert_text = f":{name}:"
        item = CompletionItem(
            label=name,
            kind=CompletionItemKind.Function,
            detail="role",
            filter_text=insert_text,
            insert_text=insert_text,
        )

        return item


def esbonio_setup(rst: RstLanguageServer):
    roles = Roles(rst)
    rst.add_feature(roles)
