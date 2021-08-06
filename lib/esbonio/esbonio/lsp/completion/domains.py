"""Completion provider for Sphinx domains."""
from typing import List

from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind

from esbonio.lsp.feature import CompletionContext
from esbonio.lsp.roles import TargetCompletion
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


def intersphinx_target_to_completion_item(
    label: str, target: tuple, type_: str
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
        insert_text=label,
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


class Domain(TargetCompletion):
    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)

    def complete_targets(self, context: CompletionContext) -> List[CompletionItem]:

        groups = context.match.groupdict()
        name = groups["name"]
        domain = groups["domain"] or None
        target = groups["target"]

        if ":" in target:
            return self.complete_intersphinx_targets(name, domain, target)

        items = [
            object_to_completion_item(o)
            for o in self.rst.get_role_targets(name, domain)
        ]

        items += [
            project_to_completion_item(p) for p in self.rst.get_intersphinx_projects()
        ]

        return items

    def complete_intersphinx_targets(
        self, name, domain, target
    ) -> List[CompletionItem]:
        items = []
        project, *_ = target.split(":")
        intersphinx_targets = self.rst.get_intersphinx_targets(project, name, domain)

        for type_, targets in intersphinx_targets.items():
            items += [
                intersphinx_target_to_completion_item(label, target, type_)
                for label, target in targets.items()
            ]

        return items
