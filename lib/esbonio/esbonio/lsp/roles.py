"""Role support."""
import re

from typing import Dict, List

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
from sphinx.domains import Domain

from esbonio.lsp import RstLanguageServer, LanguageFeature, dump
from esbonio.lsp.directives import DIRECTIVE


PARTIAL_ROLE = re.compile(
    r"""
    (^|.*[ ])            # roles must be preceeded by a space, or start the line
    (?P<role>:                    # roles start with the ':' character
    (?!:)                # make sure the next character is not ':'
    (?P<domain>[\w]+:)?  # there may be a domain namespace
    (?P<name>[\w-]*))     # match the role name
    $                    # ensure pattern only matches incomplete roles
    """,
    re.MULTILINE | re.VERBOSE,
)
"""A regular expression that matches a partial role. Used when generating auto complete
suggestions."""


def namespace_to_completion_item(namespace: str) -> CompletionItem:
    return CompletionItem(
        namespace, detail="intersphinx namespace", kind=CompletionItemKind.Module,
    )


TARGET_KINDS = {
    "attribute": CompletionItemKind.Field,
    "doc": CompletionItemKind.File,
    "class": CompletionItemKind.Class,
    "envvar": CompletionItemKind.Variable,
    "function": CompletionItemKind.Function,
    "method": CompletionItemKind.Method,
    "module": CompletionItemKind.Module,
    "py:attribute": CompletionItemKind.Field,
    "py:class": CompletionItemKind.Class,
    "py:function": CompletionItemKind.Function,
    "py:method": CompletionItemKind.Method,
    "py:module": CompletionItemKind.Module,
    "std:doc": CompletionItemKind.File,
    "std:envvar": CompletionItemKind.Variable,
    "std:term": CompletionItemKind.Text,
    "term": CompletionItemKind.Text,
}


def target_to_completion_item(name, display, type_) -> CompletionItem:
    kind = TARGET_KINDS.get(type_, CompletionItemKind.Reference)
    return CompletionItem(name, kind=kind, detail=str(display), insert_text=name)


def intersphinx_target_to_completion_item(label, item, type_) -> CompletionItem:
    kind = TARGET_KINDS.get(type_, CompletionItemKind.Reference)
    source, version, _, display = item

    if display == "-":
        display = label

    if version:
        version = f" v{version}"

    detail = f"{display} - {source}{version}"

    return CompletionItem(label, kind=kind, detail=detail, insert_text=label)


class Roles(LanguageFeature):
    """Role support for the language server."""

    def initialize(self):
        self.discover()

    def discover(self):

        # Find roles that have been registered directly with docutils
        found_roles = {**roles._roles, **roles._role_registry}

        # Find roles under Sphinx domains
        if self.rst.app is not None:

            domains = self.rst.app.registry.domains
            primary_domain = self.rst.app.config.primary_domain

            for name, domain in domains.items():
                namefmt = "{name}:{rolename}"

                # The "standard" domain and the "primary_domain" do not require
                # the namespace prefix
                if name == "std" or name == primary_domain:
                    namefmt = "{rolename}"

                found_roles.update(
                    {
                        namefmt.format(name=name, rolename=rolename): role
                        for rolename, role in domain.roles.items()
                    }
                )

        self.roles = {
            k: v for k, v in found_roles.items() if v != roles.unimplemented_role
        }

        self.logger.info("Discovered %s roles", len(self.roles))
        self.logger.debug(self.roles.keys())

    suggest_triggers = [PARTIAL_ROLE]

    def suggest(
        self, match: "re.Match", doc: Document, position: Position
    ) -> List[CompletionItem]:
        indent = match.group(1)

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


def build_role_target_map(domain: Domain) -> Dict[str, List[str]]:
    """Return a map of role names to the objects they link to.

    Parameters
    ----------
    domain:
        The Sphinx domain to build the target map for.
    """
    types = {}

    for name, obj in domain.object_types.items():
        for role in obj.roles:
            objs = types.get(role, None)

            if objs is None:
                objs = []

            objs.append(name)
            types[role] = objs

    return types


def build_target_map(domain: Domain) -> Dict[str, List[CompletionItem]]:
    """Return a map of object types to a list of completion items."""
    completion_items = {}

    for (name, disp, type_, _, _, _) in domain.get_objects():
        items = completion_items.get(type_, None)

        if items is None:
            items = []
            completion_items[type_] = items

        items.append(target_to_completion_item(name, disp, type_))

    return completion_items


class RoleTargetCompletion:
    """Completion handler for role targets."""

    def __init__(self, rst: RstLanguageServer):
        self.rst = rst

    def initialize(self):
        self.discover_target_types()
        self.discover_targets()

    def save(self, params: DidSaveTextDocumentParams):
        self.discover_targets()

    suggest_triggers = [
        re.compile(
            r"""
            (^|.*[ ])            # roles must be preceeded by a space, or start the line
            :                    # roles start with the ':' character
            (?P<name>[\w-]+)     # capture the role name, suggestions will change based on it
            :                    # the role name ends with a ':'
            `                    # the target begins with a '`'
            (?P<target>[^<:`]*)  # match "plain link" targets
            $
            """,
            re.MULTILINE | re.VERBOSE,
        ),
        re.compile(
            r"""
            (^|.*[ ])            # roles must be preceeded by a space, or start the line
            :                    # roles start with the ':' character
            (?P<name>[\w-]+)     # capture the role name, suggestions will change based on it
            :                    # the role name ends with a ':'
            `                    # the target begins with a '`'`
            .*<                  # the actual target name starts after a '<'
            (?P<target>[^`:]*)   # match "aliased" targets
            $
            """,
            re.MULTILINE | re.VERBOSE,
        ),
    ]

    def suggest(self, match, doc, position) -> List[CompletionItem]:
        # TODO: Detect if we're in an angle bracket e.g. :ref:`More Info <|` in that
        # situation, add the closing '>' to the completion item insert text.

        if match is None:
            return []

        rolename = match.group("name")
        types = self.target_types.get(rolename, None)

        if types is None:
            return []

        targets = []
        for type_ in types:
            targets += self.targets.get(type_, [])

        return targets

    def discover_target_types(self):

        if self.rst.app is None:
            return

        # TODO: Implement proper domain handling, will focus on std+python for now
        domains = self.rst.app.env.domains
        py = domains["py"]
        std = domains["std"]

        self.target_types = {**build_role_target_map(py), **build_role_target_map(std)}

    def discover_targets(self):

        if self.rst.app is None:
            self.targets = {}
            return

        # TODO: Implement proper domain handling, will focus on std+python for now
        domains = self.rst.app.env.domains
        py = domains["py"]
        std = domains["std"]

        self.targets = {**build_target_map(py), **build_target_map(std)}


class InterSphinxNamespaceCompletion:
    """Completion handler for intersphinx namespaces."""

    def __init__(self, rst: RstLanguageServer):
        self.rst = rst
        self.namespaces = {}

    def initialize(self):

        if self.rst.app and hasattr(self.rst.app.env, "intersphinx_named_inventory"):
            inv = self.rst.app.env.intersphinx_named_inventory
            self.namespaces = {v: namespace_to_completion_item(v) for v in inv.keys()}

            self.rst.logger.debug(
                "Discovered %s intersphinx namespaces", len(self.namespaces)
            )

    suggest_triggers = RoleTargetCompletion.suggest_triggers

    def suggest(self, match, doc, position) -> List[CompletionItem]:
        return list(self.namespaces.values())


def build_target_type_map(domain: Domain) -> Dict[str, List[str]]:

    types = {}

    for name, obj in domain.object_types.items():
        for role in obj.roles:
            objs = types.get(role, None)

            if objs is None:
                objs = []

            objs.append(f"{domain.name}:{name}")
            types[role] = objs

    return types


class InterSphinxTargetCompletion:
    """Completion handler for intersphinx targets"""

    def __init__(self, rst: RstLanguageServer):
        self.rst = rst
        self.targets = {}
        self.target_types = {}

    def initialize(self):

        if self.rst.app and hasattr(self.rst.app.env, "intersphinx_named_inventory"):
            inv = self.rst.app.env.intersphinx_named_inventory
            domains = self.rst.app.env.domains

            for domain in domains.values():
                self.target_types.update(build_target_type_map(domain))

            for namespace, types in inv.items():
                self.targets[namespace] = {
                    type_: {
                        label: intersphinx_target_to_completion_item(label, item, type_)
                        for label, item in items.items()
                    }
                    for type_, items in types.items()
                }

    suggest_triggers = [
        re.compile(
            r"""
            (^|.*[ ])              # roles must be preceeded by a space, or start the line
            :                      # roles start with the ':' character
            (?P<name>[\w-]+)       # capture the role name, suggestions will change based on it
            :                      # the role name ends with a ':'
            `                      # the target begins with a '`'
            (?P<namespace>[^<:]*)  # match "plain link" targets
            :                      # namespaces end with a ':'
            $
            """,
            re.MULTILINE | re.VERBOSE,
        ),
        re.compile(
            r"""
            (^|.*[ ])              # roles must be preceeded by a space, or start the line
            :                      # roles start with the ':' character
            (?P<name>[\w-]+)       # capture the role name, suggestions will change based on it
            :                      # the role name ends with a ':'
            `                      # the target begins with a '`'`
            .*<                    # the actual target name starts after a '<'
            (?P<namespace>[^:]*)   # match "aliased" targets
            :                      # namespaces end with a ':'
            $
            """,
            re.MULTILINE | re.VERBOSE,
        ),
    ]

    def suggest(self, match, doc, position) -> List[CompletionItem]:
        # TODO: Detect if we're in an angle bracket e.g. :ref:`More Info <|` in that
        # situation, add the closing '>' to the completion item insert text.

        namespace = match.group("namespace")
        rolename = match.group("name")

        types = self.target_types.get(rolename, None)
        if types is None:
            return []

        namespace = self.targets.get(namespace, None)
        if namespace is None:
            return []

        targets = []
        for type_ in types:
            items = namespace.get(type_, {})
            targets += items.values()

        return targets


def setup(rst: RstLanguageServer):
    role_completion = Roles(rst)
    role_target_completion = RoleTargetCompletion(rst)
    intersphinx_namespaces = InterSphinxNamespaceCompletion(rst)
    intersphinx_targets = InterSphinxTargetCompletion(rst)

    rst.add_feature(role_completion)
    rst.add_feature(role_target_completion)
    rst.add_feature(intersphinx_namespaces)
    rst.add_feature(intersphinx_targets)
