"""Support for Sphinx domains."""
import pathlib
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

import pygls.uris as Uri
from docutils import nodes
from docutils.parsers.rst import Directive
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.workspace import Document
from sphinx.domains import Domain

from esbonio.lsp import CompletionContext
from esbonio.lsp import DefinitionContext
from esbonio.lsp import DocumentLinkContext
from esbonio.lsp.directives import DirectiveLanguageFeature
from esbonio.lsp.directives import Directives
from esbonio.lsp.roles import RoleLanguageFeature
from esbonio.lsp.roles import Roles
from esbonio.lsp.sphinx import SphinxLanguageServer

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


class DomainHelpers:
    """Common methods that work on domains."""

    rst: SphinxLanguageServer

    @property
    def domains(self) -> Dict[str, Domain]:
        """Return a dictionary of known domains."""

        if self.rst.app is None or self.rst.app.env is None:
            return dict()

        return self.rst.app.env.domains  # type: ignore

    def get_default_domain(self, uri: str) -> Optional[str]:
        """Return the default domain for the given uri."""

        # TODO: Add support for .. default-domain::
        if self.rst.app is not None:
            return self.rst.app.config.primary_domain

        return None


class DomainDirectives(DirectiveLanguageFeature, DomainHelpers):
    """Support for directives coming from Sphinx's domains."""

    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst

        self._directives: Optional[Dict[str, Directive]] = None
        """Cache for known directives."""

    @property
    def directives(self) -> Dict[str, Directive]:

        if self._directives is not None:
            return self._directives

        directives = {}
        for prefix, domain in self.domains.items():
            for name, directive in domain.directives.items():
                directives[f"{prefix}:{name}"] = directive

        self._directives = directives
        return self._directives

    def get_implementation(
        self, directive: str, domain: Optional[str]
    ) -> Optional[Directive]:

        if domain is not None:
            return self.directives.get(f"{domain}:{directive}", None)

        if self.rst.app is None:
            return None

        # Try the default domain
        primary_domain = self.rst.app.config.primary_domain
        impl = self.directives.get(f"{primary_domain}:{directive}", None)
        if impl is not None:
            return impl

        # Try the std domain
        return self.directives.get(f"std:{directive}", None)

    def index_directives(self) -> Dict[str, Directive]:
        return self.directives

    def suggest_directives(
        self, context: CompletionContext
    ) -> Iterable[Tuple[str, Directive]]:

        # In addition to providing each directive fully qualified, we should provide a
        # suggestion for directives in the std and primary domains without the prefix.
        items = self.directives.copy()
        primary_domain = self.get_default_domain(context.doc.uri)

        for key, directive in self.directives.items():

            if key.startswith("std:"):
                items[key.replace("std:", "")] = directive
                continue

            if primary_domain and key.startswith(f"{primary_domain}:"):
                items[key.replace(f"{primary_domain}:", "")] = directive

        return items.items()

    def suggest_options(
        self, context: CompletionContext, directive: str, domain: Optional[str]
    ) -> Iterable[str]:

        impl = self.get_implementation(directive, domain)
        if impl is None:
            return []

        return impl.option_spec.keys()


class DomainRoles(RoleLanguageFeature, DomainHelpers):
    """Support for roles coming from Sphinx's domains."""

    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst

        self._roles: Optional[Dict[str, Any]] = None
        """Cache for known roles."""

        self._role_target_types: Optional[Dict[str, List[str]]] = None
        """Cache for role target types."""

    @property
    def roles(self) -> Dict[str, Any]:

        if self._roles is not None:
            return self._roles

        roles = {}
        for prefix, domain in self.domains.items():
            for name, role in domain.roles.items():
                roles[f"{prefix}:{name}"] = role

        self._roles = roles
        return self._roles

    @property
    def role_target_types(self) -> Dict[str, List[str]]:

        if self._role_target_types is not None:
            return self._role_target_types

        self._role_target_types = {}

        for prefix, domain in self.domains.items():
            fmt = "{prefix}:{name}" if prefix else "{name}"

            for name, item_type in domain.object_types.items():
                for role in item_type.roles:
                    role_key = fmt.format(name=role, prefix=prefix)
                    target_types = self._role_target_types.get(role_key, list())
                    target_types.append(name)

                    self._role_target_types[role_key] = target_types

        return self._role_target_types

    def _get_role_target_types(self, name: str, domain: str = "") -> List[str]:
        """Return a list indicating which object types a role is capable of linking
        with.
        """

        if domain:
            return self.role_target_types.get(f"{domain}:{name}", [])

        # Try the primary domain
        if self.rst.app and self.rst.app.config.primary_domain:
            key = f"{self.rst.app.config.primary_domain}:{name}"

            if key in self.role_target_types:
                return self.role_target_types[key]

        # Finally try the standard domain
        return self.role_target_types.get(f"std:{name}", [])

    def _get_role_targets(self, name: str, domain: str = "") -> List[tuple]:
        """Return a list of objects targeted by the given role.

        Parameters
        ----------
        name:
           The name of the role
        domain:
           The domain the role is a part of, if applicable.
        """

        targets: List[tuple] = []
        domain_obj: Optional[Domain] = None

        if domain:
            domain_obj = self.domains.get(domain, None)
        else:
            std = self.domains.get("std", None)
            if std and name in std.roles:
                domain_obj = std

            elif self.rst.app and self.rst.app.config.primary_domain:
                domain_obj = self.domains.get(self.rst.app.config.primary_domain, None)

        target_types = set(self._get_role_target_types(name, domain))

        if not domain_obj:
            self.rst.logger.debug(
                "Unable to find domain for role '%s:%s'", domain, name
            )
            return []

        for obj in domain_obj.get_objects():
            if obj[2] in target_types:
                targets.append(obj)

        return targets

    def get_implementation(
        self, role: str, domain: Optional[str]
    ) -> Optional[Directive]:

        if domain is not None:
            return self.roles.get(f"{domain}:{role}", None)

        if self.rst.app is None:
            return None

        # Try the default domain
        primary_domain = self.rst.app.config.primary_domain
        impl = self.roles.get(f"{primary_domain}:{role}", None)
        if impl is not None:
            return impl

        # Try the std domain
        return self.roles.get(f"std:{role}", None)

    def index_roles(self) -> Dict[str, Any]:
        return self.roles

    def suggest_roles(self, context: CompletionContext) -> Iterable[Tuple[str, Any]]:

        # In addition to providing each role fully qulaified, we should provide a
        # suggestion for directives in the std and primary domains without the prefix.
        items = self.roles.copy()
        primary_domain = self.get_default_domain(context.doc.uri)

        for key, role in self.roles.items():

            if key.startswith("std:"):
                items[key.replace("std:", "")] = role
                continue

            if primary_domain and key.startswith(f"{primary_domain}:"):
                items[key.replace(f"{primary_domain}:", "")] = role

        return items.items()

    def complete_targets(
        self, context: CompletionContext, name: str, domain: str
    ) -> List[CompletionItem]:

        label = context.match.group("label")

        # Intersphinx targets contain ':' characters.
        if ":" in label:
            return []

        return [
            object_to_completion_item(obj)
            for obj in self._get_role_targets(name, domain)
        ]

    def resolve_target_link(
        self, context: DocumentLinkContext, name: str, domain: Optional[str], label: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """``textDocument/documentLink`` support"""

        # Ignore intersphinx references.
        if ":" in label:
            return None, None

        # Other roles like :ref: do not make sense as the ``textDocument/documentLink``
        # api doesn't support specific locations like goto definition does.
        if (domain is not None and domain != "std") or name != "doc":
            return None, None

        return self.resolve_doc(context.doc, label), None

    def find_target_definitions(
        self, context: DefinitionContext, name: str, domain: str, label: str
    ) -> List[Location]:

        if not domain and name == "ref":
            return self.ref_definition(label)

        if not domain and name == "doc":
            return self.doc_definition(context.doc, label)

        return []

    def resolve_doc(self, doc: Document, label: str) -> Optional[str]:
        if self.rst.app is None:
            return None

        srcdir = self.rst.app.srcdir
        currentdir = pathlib.Path(Uri.to_fs_path(doc.uri)).parent

        if label.startswith("/"):
            path = pathlib.Path(srcdir, label[1:] + ".rst")
        else:
            path = pathlib.Path(currentdir, label + ".rst")

        if not path.exists():
            return None

        return Uri.from_fs_path(str(path))

    def doc_definition(self, doc: Document, label: str) -> List[Location]:
        """Goto definition implementation for ``:doc:`` targets"""

        uri = self.resolve_doc(doc, label)
        if not uri:
            return []

        return [
            Location(
                uri=uri,
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            )
        ]

    def ref_definition(self, label: str) -> List[Location]:
        """Goto definition implementation for ``:ref:`` targets"""

        if not self.rst.app or not self.rst.app.env:
            return []

        types = set(self._get_role_target_types("ref"))
        std = self.domains["std"]
        if std is None:
            return []

        docname = self.find_docname_for_label(label, std, types)
        if docname is None:
            return []

        path = self.rst.app.env.doc2path(docname)
        uri = Uri.from_fs_path(path)

        doctree = self.rst.get_initial_doctree(uri)
        if doctree is None:
            return []

        uri = None
        line = None

        for node in doctree.traverse(condition=nodes.target):

            if "refid" not in node:
                continue

            if doctree.nameids.get(label, "") == node["refid"]:
                uri = Uri.from_fs_path(node.source)
                line = node.line
                break

        if uri is None or line is None:
            return []

        return [
            Location(
                uri=uri,
                range=Range(
                    start=Position(line=line - 1, character=0),
                    end=Position(line=line, character=0),
                ),
            )
        ]

    def find_docname_for_label(
        self, label: str, domain: Domain, types: Optional[Set[str]] = None
    ) -> Optional[str]:
        """Given the label name and domain it belongs to, return the docname its
        definition resides in.

        Parameters
        ----------
        label
           The label to search for

        domain
           The domain to search within

        types
           A collection of object types that the label chould have.
        """

        docname = None
        types = types or set()

        # _, title, _, _, anchor, priority
        for name, _, type_, doc, _, _ in domain.get_objects():
            if types and type_ not in types:
                continue

            if name == label:
                docname = doc
                break

        return docname


class Intersphinx(RoleLanguageFeature):
    def __init__(self, rst: SphinxLanguageServer, domain: DomainRoles):
        self.rst = rst
        self.domain = domain

    def complete_targets(
        self, context: CompletionContext, name: str, domain: str
    ) -> List[CompletionItem]:

        label = context.match.group("label")

        # Intersphinx targets contain ':' characters.
        if ":" in label:
            return self.complete_intersphinx_targets(name, domain, label)

        return self.complete_intersphinx_projects(name, domain)

    def complete_intersphinx_projects(
        self, name: str, domain: str
    ) -> List[CompletionItem]:

        items = []
        for project in self.get_intersphinx_projects():
            if not self.has_intersphinx_targets(project, name, domain):
                continue

            items.append(
                CompletionItem(
                    label=project, detail="intersphinx", kind=CompletionItemKind.Module
                )
            )

        return items

    def complete_intersphinx_targets(
        self, name: str, domain: str, label: str
    ) -> List[CompletionItem]:
        items = []
        project, *_ = label.split(":")
        intersphinx_targets = self.get_intersphinx_targets(project, name, domain)

        for type_, targets in intersphinx_targets.items():
            items += [
                intersphinx_target_to_completion_item(project, label, target, type_)
                for label, target in targets.items()
            ]

        return items

    def resolve_target_link(
        self, context: DocumentLinkContext, name: str, domain: Optional[str], label: str
    ) -> Tuple[Optional[str], Optional[str]]:

        if not self.rst.app:
            return None, None

        project, *parts = label.split(":")
        label = ":".join(parts)
        targets = self.get_intersphinx_targets(project, name, domain or "")

        for _, items in targets.items():
            if label in items:
                source, version, url, display = items[label]
                name = label if display == "-" else display
                tooltip = f"{name} - {source} v{version}"

                return url, tooltip

        return None, None

    def get_intersphinx_projects(self) -> List[str]:
        """Return the list of configured intersphinx project names."""

        if self.rst.app is None:
            return []

        inv = getattr(self.rst.app.env, "intersphinx_named_inventory", {})
        return list(inv.keys())

    def has_intersphinx_targets(
        self, project: str, name: str, domain: str = ""
    ) -> bool:
        """Return ``True`` if the given intersphinx project has targets targeted by the
        given role.

        Parameters
        ----------
        project
           The project to check

        name
           The name of the role

        domain
           The domain the role is a part of, if applicable.
        """
        targets = self.get_intersphinx_targets(project, name, domain)

        if len(targets) == 0:
            return False

        return any([len(items) > 0 for items in targets.values()])

    def get_intersphinx_targets(
        self, project: str, name: str, domain: str = ""
    ) -> Dict[str, Dict[str, tuple]]:
        """Return the intersphinx objects targeted by the given role.

        Parameters
        ----------
        project
           The project to return targets from

        name
           The name of the role

        domain
           The domain the role is a part of, if applicable.
        """

        if self.rst.app is None:
            return {}

        inv = getattr(self.rst.app.env, "intersphinx_named_inventory", {})
        if project not in inv:
            return {}

        targets = {}
        inv = inv[project]

        for target_type in self.domain._get_role_target_types(name, domain):

            explicit_domain = f"{domain}:{target_type}"
            if explicit_domain in inv:
                targets[target_type] = inv[explicit_domain]
                continue

            primary_domain = f'{self.rst.app.config.primary_domain or ""}:{target_type}'
            if primary_domain in inv:
                targets[target_type] = inv[primary_domain]
                continue

            std_domain = f"std:{target_type}"
            if std_domain in inv:
                targets[target_type] = inv[std_domain]

        return targets


def intersphinx_target_to_completion_item(
    project: str, label: str, target: tuple, type_: str
) -> CompletionItem:

    # _. _. url, _
    source, version, _, display = target

    display_name = label if display == "-" else display
    completion_kind = ":".join(type_.split(":")[1:]) if ":" in type_ else type_

    if version:
        version = f" v{version}"

    return CompletionItem(
        label=label,
        detail=f"{display_name} - {source}{version}",
        kind=TARGET_KINDS.get(completion_kind, CompletionItemKind.Reference),
        insert_text=f"{project}:{label}",
    )


def object_to_completion_item(object_: tuple) -> CompletionItem:

    # _, _, _, docname, anchor, priority
    name, display_name, type_, _, _, _ = object_
    insert_text = name

    key = type_.split(":")[1] if ":" in type_ else type_
    kind = TARGET_KINDS.get(key, CompletionItemKind.Reference)

    # ensure :doc: targets are inserted as an absolute path - that way the reference
    # will always work regardless of the file's location.
    if type_ == "doc":
        insert_text = f"/{name}"

    # :option: targets need to be inserted as `<progname> <option>` in order to resolve
    # correctly. However, this only seems to be the case "locally" as
    # `<progname>.<option>` seems to resolve fine when using intersphinx...
    if type_ == "cmdoption":
        name = " ".join(name.split("."))
        display_name = name
        insert_text = name

    return CompletionItem(
        label=name, kind=kind, detail=str(display_name), insert_text=insert_text
    )


def esbonio_setup(rst: SphinxLanguageServer, directives: Directives, roles: Roles):
    directives.add_feature(DomainDirectives(rst))

    domain_roles = DomainRoles(rst)
    intersphinx = Intersphinx(rst, domain_roles)

    roles.add_feature(domain_roles)
    roles.add_feature(intersphinx)
