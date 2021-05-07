"""Completion handler for filepaths.

While :mod:`esbonio.lsp.roles` and :mod:`esbonio.lsp.directives` provide generic
completion handlers for roles and directives, similar to :mod:`esbonio.lsp.intersphinx`
this is a "specialised" module dedicated to providing completion suggestions just for
the roles or directives that accept filepaths as arguments.
"""
import pathlib
import re

from typing import Dict, List

from pygls.lsp.types import CompletionItem, CompletionItemKind, Position
from pygls.workspace import Document

import esbonio.lsp as lsp
from esbonio.lsp import RstLanguageServer, LanguageFeature
from esbonio.lsp.directives import DIRECTIVE
from esbonio.lsp.roles import PARTIAL_PLAIN_TARGET, PARTIAL_ALIASED_TARGET

# TODO: Would it be better to make the role and directive language features extensible
#       and have this and the intersphinx feature contribute suggestions when they know
#       something?..
class FilepathCompletions(LanguageFeature):
    """Filepath completion support."""

    suggest_triggers = [DIRECTIVE, PARTIAL_PLAIN_TARGET, PARTIAL_ALIASED_TARGET]

    def suggest(
        self, match: "re.Match", doc: Document, position: Position
    ) -> List[CompletionItem]:

        groups = match.groupdict()

        if not self.should_suggest(groups):
            return []

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
            filepath = lsp.filepath_from_uri(doc.uri)
            candidate_dir = pathlib.Path(filepath).parent

        candidate_dir /= pathlib.Path(partial_path)

        if partial_path and not partial_path.endswith("/"):
            candidate_dir = candidate_dir.parent

        return [self.path_to_completion_item(p) for p in candidate_dir.glob("*")]

    def should_suggest(self, groups: Dict[str, str]) -> bool:
        """Determines if we should make any suggestions."""

        roles = {"download"}
        directives = {"image", "figure", "include", "literalinclude"}

        return any(
            [
                groups["name"] in roles and "role" in groups,
                groups["name"] in directives and "directive" in groups,
            ]
        )

    def path_to_completion_item(self, path: pathlib.Path) -> CompletionItem:

        kind = CompletionItemKind.Folder if path.is_dir() else CompletionItemKind.File
        return CompletionItem(
            label=str(path.name), kind=kind, insert_text=f"{path.name}",
        )


def setup(rst: RstLanguageServer):
    filepaths = FilepathCompletions(rst)
    rst.add_feature(filepaths)
