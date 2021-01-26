"""Role completions."""
import re

from typing import Dict, List

from docutils.parsers.rst import roles
from pygls.types import CompletionItem, CompletionItemKind, DidSaveTextDocumentParams
from sphinx.domains import Domain

from esbonio.lsp import RstLanguageServer


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


class RoleCompletion:
    """Completion handler for roles."""

    def __init__(self, rst: RstLanguageServer):
        self.rst = rst

    def initialize(self):
        self.discover()

    def discover(self):

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

        if self.rst.app is not None:

            # Find roles that are held in a Sphinx domain.
            # TODO: Implement proper domain handling, will focus on std+python for now
            domains = self.rst.app.registry.domains
            std_roles = domains["std"].roles
            py_roles = domains["py"].roles

        rs = {**local_roles, **role_registry, **std_roles, **py_roles}

        self.roles = {k: role_to_completion_item(k, v) for k, v in rs.items()}
        self.rst.logger.debug("Discovered %s roles", len(self.roles))

    suggest_trigger = re.compile(
        r"""
        (^|.*[ ])  # roles must be preceeded by a space, or start the line
        :          # roles start with the ':' character
        (?!:)      # make sure the next character is not ':'
        [\w-]*     # match the role name
        $          # ensure pattern only matches incomplete roles
        """,
        re.MULTILINE | re.VERBOSE,
    )

    def suggest(self, match, line, doc) -> List[CompletionItem]:
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


class RoleTargetCompletion:
    """Completion handler for role targets."""

    def __init__(self, rst: RstLanguageServer):
        self.rst = rst

    def initialize(self):
        self.discover_target_types()
        self.discover_targets()

    def save(self, params: DidSaveTextDocumentParams):
        self.discover_targets()

    suggest_trigger = re.compile(
        r"""
        (^|.*[ ])          # roles must be preveeded by a space, or start the line
        :                 # roles start with the ':' character
        (?P<name>[\w-]+)  # capture the role name, suggestions will change based on it
        :                 # the role name ends with a ':'
        `                 # the target begins with a '`'`
        """,
        re.MULTILINE | re.VERBOSE,
    )

    def suggest(self, match, line, doc) -> List[CompletionItem]:
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


def setup(rst: RstLanguageServer):
    role_completion = RoleCompletion(rst)
    role_target_completion = RoleTargetCompletion(rst)

    rst.add_feature(role_completion)
    rst.add_feature(role_target_completion)
