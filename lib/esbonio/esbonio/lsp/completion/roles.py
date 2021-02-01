"""Role completions."""
import re

from typing import Dict, List

from docutils.parsers.rst import roles
from pygls.types import CompletionItem, CompletionItemKind, DidSaveTextDocumentParams
from sphinx.domains import Domain

from esbonio.lsp import RstLanguageServer


def namespace_to_completion_item(namespace: str) -> CompletionItem:
    return CompletionItem(
        namespace,
        detail="intersphinx namespace",
        kind=CompletionItemKind.Module,
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

    suggest_triggers = [
        re.compile(
            r"""
            (^|.*[ ])  # roles must be preceeded by a space, or start the line
            :          # roles start with the ':' character
            (?!:)      # make sure the next character is not ':'
            [\w-]*     # match the role name
            $          # ensure pattern only matches incomplete roles
            """,
            re.MULTILINE | re.VERBOSE,
        )
    ]

    def suggest(self, match, doc, position) -> List[CompletionItem]:
        indent = match.group(1)

        # If there's no indent, then this can only be a role defn
        if indent == "":
            return list(self.roles.values())

        # Otherwise, search backwards until we find a blank line or an unindent
        # so that we can determine the appropriate context.
        linum = position.line - 1
        line = doc.lines[linum]

        while line.startswith(indent):
            linum -= 1
            line = doc.lines[linum]

        # Unless we are within a directive's options block, we should offer role
        # suggestions
        if re.match(r"\s*\.\.[ ]*([\w-]+)::", line):
            return []

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
    role_completion = RoleCompletion(rst)
    role_target_completion = RoleTargetCompletion(rst)
    intersphinx_namespaces = InterSphinxNamespaceCompletion(rst)
    intersphinx_targets = InterSphinxTargetCompletion(rst)

    rst.add_feature(role_completion)
    rst.add_feature(role_target_completion)
    rst.add_feature(intersphinx_namespaces)
    rst.add_feature(intersphinx_targets)
