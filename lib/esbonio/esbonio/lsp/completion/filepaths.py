"""Completion provider for filepaths."""
import pathlib
from typing import List

import pygls.uris as uri
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import TextEdit

from esbonio.lsp.directives import ArgumentCompletion
from esbonio.lsp.roles import TargetCompletion
from esbonio.lsp.rst import CompletionContext
from esbonio.lsp.sphinx import SphinxLanguageServer


def path_to_completion_item(
    context: CompletionContext, path: pathlib.Path
) -> CompletionItem:
    """Create the ``CompletionItem`` for the given path.

    In the case where there are multiple filepath components, this function needs to
    provide an appropriate ``TextEdit`` so that the most recent entry in the path can
    be easily edited - without clobbering the existing path.

    Also bear in mind that this function must play nice with both role target and
    directive argument completions.
    """

    new_text = f"{path.name}"
    kind = CompletionItemKind.Folder if path.is_dir() else CompletionItemKind.File

    # If we can't find the '/' we may as well not bother with a `TextEdit` and let the
    # `Roles` feature provide the default handling.
    start = find_start_char(context)
    if start == -1:
        insert_text = new_text
        filter_text = None
        text_edit = None
    else:

        start += 1
        _, end = context.match.span()
        prefix = context.match.group(0)[start:]

        insert_text = None
        filter_text = (
            f"{prefix}{new_text}"  # Needed so VSCode will actually show the results.
        )

        text_edit = TextEdit(
            range=Range(
                start=Position(line=context.position.line, character=start),
                end=Position(line=context.position.line, character=end),
            ),
            new_text=new_text,
        )

    return CompletionItem(
        label=new_text,
        kind=kind,
        insert_text=insert_text,
        filter_text=filter_text,
        text_edit=text_edit,
    )


def find_start_char(context: CompletionContext) -> int:
    matched_text = context.match.group(0)
    idx = matched_text.find("/")

    while True:
        next_idx = matched_text.find("/", idx + 1)
        if next_idx == -1:
            break

        idx = next_idx

    return idx


class Filepath(ArgumentCompletion, TargetCompletion):
    """Filepath completion support."""

    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)

    def complete_arguments(self, context: CompletionContext) -> List[CompletionItem]:

        name = context.match.groupdict()["name"]
        if name in {"image", "figure", "include", "literalinclude"}:
            return self.complete_filepaths(context)

    def complete_targets(
        self, context: CompletionContext, domain: str, name: str
    ) -> List[CompletionItem]:

        if name in {"download"}:
            return self.complete_filepaths(context)

    def complete_filepaths(self, context: CompletionContext) -> List[CompletionItem]:

        groups = context.match.groupdict()

        if "role" in groups:
            partial_path = groups["label"]
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
            filepath = uri.to_fs_path(context.doc.uri)
            candidate_dir = pathlib.Path(filepath).parent

        candidate_dir /= pathlib.Path(partial_path)

        if partial_path and not partial_path.endswith("/"):
            candidate_dir = candidate_dir.parent

        return [path_to_completion_item(context, p) for p in candidate_dir.glob("*")]
