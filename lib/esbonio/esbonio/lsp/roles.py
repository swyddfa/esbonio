"""Role support."""
import collections
import re

from typing import List

from docutils.parsers.rst import roles
from pygls.types import (
    CompletionItem,
    CompletionItemKind,
    DidSaveTextDocumentParams,
    Position,
    Range,
    TextEdit,
)
from pygls.workspace import Document

from esbonio.lsp import RstLanguageServer, LanguageFeature, dump
from esbonio.lsp.directives import DIRECTIVE
from esbonio.lsp.sphinx import get_domains


PARTIAL_ROLE = re.compile(
    r"""
    (^|.*[ ])            # roles must be preceeded by a space, or start the line
    (?P<role>:           # roles start with the ':' character
    (?!:)                # make sure the next character is not ':'
    (?P<domain>[\w]+:)?  # there may be a domain namespace
    (?P<name>[\w-]*))    # match the role name
    $                    # ensure pattern only matches incomplete roles
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
    (^|.*[ ])            # roles must be preceeded by a space, or start the line
    (?P<role>:           # roles start with the ':' character
    (?!:)                # make sure the next character is not ':'
    (?P<domain>[\w]+:)?  # there may be a domain namespace
    (?P<name>[\w-]*)     # followed by the role name
    :)                   # the role name ends with a ':'
    `                    # the target begins with a '`'
    (?P<target>[^<:`]*)  # match "plain link" targets
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
    (^|.*[ ])            # roles must be preceeded by a space, or start the line
    (?P<role>:           # roles start with the ':' character
    (?!:)                # make sure the next character is not ':'
    (?P<domain>[\w]+:)?  # there may be a domain namespace
    (?P<name>[\w-]*)     # followed by the role name
    :)                   # the role name ends with a ':'
    `                    # the target begins with a '`'`
    .*<                  # the actual target name starts after a '<'
    (?P<target>[^`:]*)   # match "aliased" targets
    $
    """,
    re.MULTILINE | re.VERBOSE,
)
"""A regular expression that matches an "aliased" role target.

For example::

   :ref:`More info <som

Used when generating auto complete suggestions.
"""


CompletionTarget = collections.namedtuple("CompletionTarget", "kind,insert_fmt")

DEFAULT_TARGET = CompletionTarget(CompletionItemKind.Reference, "{name}")
COMPLETION_TARGETS = {
    "attribute": CompletionTarget(CompletionItemKind.Field, "{name}"),
    "doc": CompletionTarget(CompletionItemKind.File, "/{name}"),
    "class": CompletionTarget(CompletionItemKind.Class, "{name}"),
    "envvar": CompletionTarget(CompletionItemKind.Variable, "{name}"),
    "function": CompletionTarget(CompletionItemKind.Function, "{name}"),
    "method": CompletionTarget(CompletionItemKind.Method, "{name}"),
    "module": CompletionTarget(CompletionItemKind.Module, "{name}"),
    "term": CompletionTarget(CompletionItemKind.Text, "{name}"),
}


class Roles(LanguageFeature):
    """Role support for the language server."""

    def initialize(self):
        self.discover_roles()
        self.discover_targets()

    def save(self, params: DidSaveTextDocumentParams):
        self.discover_targets()

    def discover_roles(self):
        """Look up for valid role defintions to to offer as autocomplete suggestions.

        *This method only needs to be called once per application instance.*

        This will look for all the roles registered with docutils as well as the
        roles that are stored on a Sphinx domain object.

        Additionally, while we are looping through the domain objects, we construct
        the ``target_types`` dictionary. This is used when providing role target
        completions by giving the list of object types the current role is able to
        link with.

        For example, consider the :rst:role:`sphinx:py:func` and
        :rst:role:`sphinx:py:class` roles from the Python domain. As the ``func`` role
        links to Python functions and the ``class`` role links to Python classes *and*
        exceptions we would end up with

        .. code-block:: python

           {
             "func": ["py:function"],
             "class": ["py:class", "py:exception"]
           }

        """

        # Find roles that have been registered directly with docutils
        self.target_types = {}
        found_roles = {**roles._roles, **roles._role_registry}

        # Find roles under Sphinx domains
        for prefix, domain in get_domains(self.rst.app):
            fmt = "{prefix}:{name}" if prefix else "{name}"

            for name, role in domain.roles.items():
                key = fmt.format(name=name, prefix=prefix)
                found_roles[key] = role

            # Also build a map we can use when looking up target completions.
            for name, item_type in domain.object_types.items():
                for role in item_type.roles:
                    key = fmt.format(name=role, prefix=prefix)
                    target_types = self.target_types.get(key, None)

                    if target_types is None:
                        target_types = []

                    target_types.append(fmt.format(name=name, prefix=prefix))
                    self.target_types[key] = target_types

        self.roles = {
            k: v for k, v in found_roles.items() if v != roles.unimplemented_role
        }

        self.logger.info("Discovered %s roles", len(self.roles))
        self.logger.debug("Roles: %s", list(self.roles.keys()))

        self.logger.info("Discovered %s target types", len(self.target_types))
        self.logger.debug("Target types: %s", self.target_types)

    def discover_targets(self):
        """Look up all the targets we can offer as autocomplete suggestions.

        *This method needs to be called each time a document has been saved.*
        """
        self.target_objects = {}

        for prefix, domain in get_domains(self.rst.app):
            fmt = "{prefix}:{name}" if prefix else "{name}"

            for (name, display_name, obj_type, _, _, _) in domain.get_objects():
                key = fmt.format(name=obj_type, prefix=prefix)
                items = self.target_objects.get(key, None)

                if items is None:
                    items = []
                    self.target_objects[key] = items

                items.append(
                    self.target_object_to_completion_item(name, display_name, obj_type)
                )

    suggest_triggers = [PARTIAL_ROLE, PARTIAL_PLAIN_TARGET, PARTIAL_ALIASED_TARGET]

    def suggest(
        self, match: "re.Match", doc: Document, position: Position
    ) -> List[CompletionItem]:
        indent = match.group(1)

        if "target" in match.groupdict():
            return self.suggest_targets(match, position)

        # If there's no indent, then this can only be a role defn
        if indent == "":
            return self.suggest_roles(match, position)

        # Otherwise, search backwards until we find a blank line or an unindent
        # so that we can determine the appropriate context.
        linum = position.line - 1

        try:
            line = doc.lines[linum]
        except IndexError:
            return self.suggest_roles(match, position)

        while line.startswith(indent):
            linum -= 1
            line = doc.lines[linum]

        # Unless we are within a directive's options block, we should offer role
        # suggestions
        if DIRECTIVE.match(line):
            return []

        return self.suggest_roles(match, position)

    def suggest_roles(
        self, match: "re.Match", position: Position
    ) -> List[CompletionItem]:
        self.logger.info("Suggesting roles")

        domain = match.groupdict()["domain"] or ""
        items = []

        for name, role in self.roles.items():

            if not name.startswith(domain):
                continue

            item = self.role_to_completion_item(name, role, match, position)
            items.append(item)

        return items

    def suggest_targets(
        self, match: "re.Match", position: Position
    ) -> List[CompletionItem]:

        self.logger.info("Suggesting targets")

        groups = match.groupdict()
        domain = groups["domain"] or ""
        key = f"{domain}{groups['name']}"

        object_types = self.target_types.get(key, None)

        self.logger.debug("Getting suggestions for '%s'", key)
        self.logger.debug("Role targets object types: %s", object_types)

        if object_types is None:
            return []

        targets = []
        for type_ in object_types:
            targets += self.target_objects.get(type_, [])

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
            name,
            kind=CompletionItemKind.Function,
            filter_text=insert_text,
            detail="role",
            text_edit=TextEdit(
                range=Range(Position(line, start), Position(line, end)),
                new_text=insert_text,
            ),
        )

        self.logger.debug("Item %s", dump(item))
        return item

    def target_object_to_completion_item(
        self, name: str, display_name: str, obj_type: str
    ) -> CompletionItem:
        """Convert a target object to its CompletionItem representation."""

        key = obj_type

        if ":" in key:
            _, key = key.split(":")

        target_type = COMPLETION_TARGETS.get(key, DEFAULT_TARGET)

        return CompletionItem(
            name,
            kind=target_type.kind,
            detail=str(display_name),
            insert_text=target_type.insert_fmt.format(name=name),
        )


def setup(rst: RstLanguageServer):
    role_completion = Roles(rst)
    rst.add_feature(role_completion)
