"""Completion provider for filepaths."""
import pathlib
import re
from typing import List

import pygls.uris as uri
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.workspace import Document

from esbonio.lsp.directives import ArgumentCompletion
from esbonio.lsp.feature import CompletionContext
from esbonio.lsp.roles import TargetCompletion
from esbonio.lsp.sphinx import SphinxLanguageServer


def path_to_completion_item(path: pathlib.Path) -> CompletionItem:

    kind = CompletionItemKind.Folder if path.is_dir() else CompletionItemKind.File
    return CompletionItem(
        label=str(path.name),
        kind=kind,
        insert_text=f"{path.name}",
    )


class Filepath(ArgumentCompletion, TargetCompletion):
    """Filepath completion support."""

    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)

    def complete_arguments(self, context: CompletionContext) -> List[CompletionItem]:

        name = context.match.groupdict()["name"]
        if name in {"image", "figure", "include", "literalinclude"}:
            return self.complete_filepaths(context.doc, context.match)

    def complete_targets(self, context: CompletionContext) -> List[CompletionItem]:

        name = context.match.groupdict()["name"]
        if name in {"download"}:
            return self.complete_filepaths(context.doc, context.match)

    def complete_filepaths(
        self, doc: Document, match: "re.Match"
    ) -> List[CompletionItem]:

        groups = match.groupdict()

        if "target" in groups:
            partial_path = groups["target"]
        else:
            partial_path = groups["argument"]

        if partial_path.startswith("/"):
            # Absolute paths are relative to the top level source dir.
            candidate_dir = pathlib.Path(self.rst.app.srcdir)

            # Be sure to take off the leading '/' character, otherwise the partial
            # path will wipe out the srcdir part when concatenated..
            partial_path = partial_path[1:]
        else:
            # Otherwise they're relative to the current file.
            filepath = uri.to_fs_path(doc.uri)
            candidate_dir = pathlib.Path(filepath).parent

        candidate_dir /= pathlib.Path(partial_path)

        if partial_path and not partial_path.endswith("/"):
            candidate_dir = candidate_dir.parent

        return [path_to_completion_item(p) for p in candidate_dir.glob("*")]
