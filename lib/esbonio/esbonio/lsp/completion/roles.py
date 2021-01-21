"""Role completions."""
from __future__ import annotations

import re

from typing import Dict, List

from docutils.parsers.rst import roles
from pygls.types import CompletionItem, CompletionItemKind
from sphinx.application import Sphinx
from sphinx.domains import Domain

from esbonio.lsp.completion import CompletionHandler

# This should match someone typing out a new role e.g. :re|
ROLE = re.compile(
    r"""(^|.*[ ])  # roles must be preceeded by a space, or start the line
        :          # roles start with the ':' character
        (?!:)      # make sure the next character is not ':'
        [\w-]*     # match the role name
        $          # ensure pattern only matches incomplete roles
    """,
    re.MULTILINE | re.VERBOSE,
)


# This should match someone typing out a role target e.g. :ref:`ti|
#                                                         :ref:`more info <ti|
ROLE_TARGET = re.compile(
    r"""(^|.*[ ])          # roles must be preveeded by a space, or start the line
        :                 # roles start with the ':' character
        (?P<name>[\w-]+)  # capture the role name, suggestions will change based on it
        :                 # the role name ends with a ':'
        `                 # the target begins with a '`'`
    """,
    re.MULTILINE | re.VERBOSE,
)


def role_to_completion_item(name, role) -> CompletionItem:
    return CompletionItem(
        name,
        kind=CompletionItemKind.Function,
        detail="role",
        insert_text="{}:".format(name),
    )


TARGET_KINDS = {
    "attribute": CompletionItemKind.Field,
    "doc": CompletionItemKind.File,
    "class": CompletionItemKind.Class,
    "envvar": CompletionItemKind.Variable,
    "function": CompletionItemKind.Function,
    "method": CompletionItemKind.Method,
    "module": CompletionItemKind.Module,
    "term": CompletionItemKind.Text,
}


def target_to_completion_item(name, display, type_) -> CompletionItem:
    kind = TARGET_KINDS.get(type_, CompletionItemKind.Reference)
    return CompletionItem(name, kind=kind, detail=str(display), insert_text=name)


class RoleHandler(CompletionHandler):
    """Completion handler for roles."""

    def __init__(self, app: Sphinx):

        # Find roles that have been registered directly with docutils
        local_roles = {
            k: v for k, v in roles._roles.items() if v != roles.unimplemented_role
        }
        role_registry = {
            k: v
            for k, v in roles._role_registry.items()
            if v != roles.unimplemented_role
        }
        std_roles = {}
        py_roles = {}

        if app is not None:

            # Find roles that are held in a Sphinx domain.
            # TODO: Implement proper domain handling, will focus on std+python for now
            domains = app.registry.domains
            std_roles = domains["std"].roles
            py_roles = domains["py"].roles

        rs = {**local_roles, **role_registry, **std_roles, **py_roles}
        self.roles = {k: role_to_completion_item(k, v) for k, v in rs.items()}

    def suggest(self, rst, match, line, doc):
        return list(self.roles.values())


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


class RoleTargetHandler(CompletionHandler):
    """Completion handler for role targets."""

    def __init__(self, app: Sphinx):

        if app is None:
            return

        # TODO: Implement proper domain handling, will focus on std+python for now
        domains = app.env.domains
        py = domains["py"]
        std = domains["std"]

        self.target_types = {**build_role_target_map(py), **build_role_target_map(std)}
        self.discover_targets(app)

    def discover_targets(self, app: Sphinx):
        """Discover possible completion targets given an application instance."""

        if app is None:
            self.targets = {}
            return

        # TODO: Implement proper domain handling, will focus on std+python for now
        domains = app.env.domains
        py = domains["py"]
        std = domains["std"]

        self.targets = {**build_target_map(py), **build_target_map(std)}

    def suggest(self, rst, match, line, doc) -> List[CompletionItem]:
        # TODO: Detect if we're in an angle bracket e.g. :ref:`More Info <|` in that
        # situation, add the closing '>' to the completion item insert text.

        if match is None:
            return []

        rolename = match.group("name")
        types = self.target_types.get(rolename, None)

        if types is None:
            return None

        targets = []
        for type_ in types:
            targets += self.targets.get(type_, [])

        return targets


def init(rst: RstLanguageServer):
    role_handler = RoleHandler(rst.app)
    role_target_handler = RoleTargetHandler(rst.app)

    rst.logger.debug("Discovered %s roles", len(role_handler.roles))
    rst.add_completion_handler(ROLE, role_handler)
    rst.add_completion_handler(ROLE_TARGET, role_target_handler)
