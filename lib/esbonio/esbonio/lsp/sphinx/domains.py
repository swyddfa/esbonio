"""Support for Sphinx domains."""
import pathlib
import typing
from typing import List
from typing import Optional
from typing import Set

import pygls.uris as Uri
from docutils import nodes
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.workspace import Document
from sphinx.domains import Domain

from esbonio.lsp.roles import Roles
from esbonio.lsp.rst import CompletionContext
from esbonio.lsp.rst import DefinitionContext
from esbonio.lsp.rst import RstLanguageServer
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


class DomainFeatures:
    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)

    def complete_targets(
        self, context: CompletionContext, name: str, domain: Optional[str]
    ) -> List[CompletionItem]:

        groups = context.match.groupdict()
        domain = domain or ""
        label = groups["label"]

        if ":" in label:
            return self.complete_intersphinx_targets(name, domain, label)

        items = [
            object_to_completion_item(o)
            for o in self.rst.get_role_targets(name, domain)
        ]

        for project in self.rst.get_intersphinx_projects():
            if self.rst.has_intersphinx_targets(project, name, domain):
                items.append(project_to_completion_item(project))

        return items

    def complete_intersphinx_targets(
        self, name: str, domain: str, label: str
    ) -> List[CompletionItem]:
        items = []
        project, *_ = label.split(":")
        intersphinx_targets = self.rst.get_intersphinx_targets(project, name, domain)

        for type_, targets in intersphinx_targets.items():
            items += [
                intersphinx_target_to_completion_item(project, label, target, type_)
                for label, target in targets.items()
            ]

        return items

    def find_definitions(
        self, context: DefinitionContext, name: str, domain: Optional[str]
    ) -> List[Location]:

        label = context.match.group("label")

        if not domain and name == "ref":
            return self.ref_definition(label)

        if not domain and name == "doc":
            return self.doc_definition(context.doc, label)

        return []

    def doc_definition(self, doc: Document, label: str) -> List[Location]:
        """Goto definition implementation for ``:doc:`` targets"""

        if self.rst.app is None:
            return []

        srcdir = self.rst.app.srcdir
        currentdir = pathlib.Path(Uri.to_fs_path(doc.uri)).parent

        if label.startswith("/"):
            path = str(pathlib.Path(srcdir, label[1:] + ".rst"))
        else:
            path = str(pathlib.Path(currentdir, label + ".rst"))

        return [
            Location(
                uri=Uri.from_fs_path(path),
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            )
        ]

    def ref_definition(self, label: str) -> List[Location]:
        """Goto definition implementation for ``:ref:`` targets"""

        types = set(self.rst.get_role_target_types("ref"))
        std = self.rst.get_domain("std")
        if std is None:
            return []

        docname = self.find_docname_for_label(label, std, types)
        if docname is None:
            return []

        doctree = self.rst.get_doctree(docname=docname)
        if doctree is None:
            return []

        uri = None
        line = None

        for node in doctree.traverse(condition=nodes.target):

            if "refid" not in node:
                continue

            if label == node["refid"].replace("-", "_"):
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
        label:
           The label to search for
        domain:
           The domain to search within
        types:
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


def project_to_completion_item(project: str) -> CompletionItem:
    return CompletionItem(
        label=project, detail="intersphinx", kind=CompletionItemKind.Module
    )


def esbonio_setup(rst: RstLanguageServer):

    if isinstance(rst, SphinxLanguageServer):
        domains = DomainFeatures(rst)
        roles = rst.get_feature("esbonio.lsp.roles.Roles")

        if roles:
            typing.cast(Roles, roles).add_target_definition_provider(domains)
            typing.cast(Roles, roles).add_target_completion_provider(domains)
