from __future__ import annotations

import pathlib
import typing

from lsprotocol import types as lsp

from esbonio import server

if typing.TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any


class DirectiveArgumentProvider:
    """Base class for directive argument providers."""

    def __init__(self, esbonio: server.EsbonioLanguageServer):
        self.converter = esbonio.converter
        self.logger = esbonio.logger.getChild(self.__class__.__name__)

    def suggest_arguments(
        self, context: server.CompletionContext, **kwargs
    ) -> (
        list[lsp.CompletionItem]
        | None
        | Coroutine[Any, Any, list[lsp.CompletionItem] | None]
    ):
        """Given a completion context, suggest directive arguments that may be used."""
        return None


class ValuesProvider(DirectiveArgumentProvider):
    """Simple completions provider that supports a static list of values."""

    def suggest_arguments(  # type: ignore[override]
        self, context: server.CompletionContext, *, values: list[str | dict[str, Any]]
    ) -> list[lsp.CompletionItem]:
        """Given a completion context, suggest directive arguments that may be used."""
        result: list[lsp.CompletionItem] = []

        for value in values:
            if isinstance(value, str):
                result.append(lsp.CompletionItem(label=value))
                continue

            try:
                result.append(self.converter.structure(value, lsp.CompletionItem))
            except Exception:
                self.logger.exception("Unable to create CompletionItem")

        return result


class FilepathProvider(DirectiveArgumentProvider):
    """Argument provider for filepaths."""

    def suggest_arguments(  # type: ignore[override]
        self,
        context: server.CompletionContext,
        *,
        root: str = "/",
        pattern: str | None = None,
    ) -> list[lsp.CompletionItem]:
        """Given a completion context, suggest files (or folders) that may be used.

        Parameters
        ----------
        root
           If the user provides an absolute path, generate suggestions relative to this directory.

        pattern
           If set, limit suggestions only to matching files.

        Returns
        -------
        list[lsp.CompletionItem]
           A list of completion items to suggest.
        """
        uri = server.Uri.parse(context.doc.uri)
        cwd = pathlib.Path(uri).parent

        if (partial := context.match.group("argument")) and partial.startswith("/"):
            candidate_dir = pathlib.Path(root)

            # Be sure to remove the leading '/', otherwise partial will wipe out the
            # root when concatenated.
            partial = partial[1:]
        else:
            candidate_dir = cwd

        candidate_dir /= partial
        if partial and not partial.endswith(("/", ".")):
            candidate_dir = candidate_dir.parent

        self.logger.debug("Suggesting files relative to %r", candidate_dir)
        return [
            self._path_to_completion_item(context, p) for p in candidate_dir.glob("*")
        ]

    def _path_to_completion_item(
        self, context: server.CompletionContext, path: pathlib.Path
    ) -> lsp.CompletionItem:
        """Create the ``CompletionItem`` for the given path.

        In the case where there are multiple filepath components, this function needs to
        provide an appropriate ``TextEdit`` so that the most recent entry in the path can
        be easily edited - without clobbering the existing path.

        Also bear in mind that this function must play nice with both role target and
        directive argument completions.
        """

        new_text = f"{path.name}"
        kind = (
            lsp.CompletionItemKind.Folder
            if path.is_dir()
            else lsp.CompletionItemKind.File
        )

        if (start := self._find_start_char(context)) == -1:
            insert_text = new_text
            filter_text = None
            text_edit = None
        else:
            start += 1
            _, end = context.match.span()
            prefix = context.match.group(0)[start:]

            insert_text = None
            filter_text = f"{prefix}{new_text}"  # Needed so VSCode will actually show the results.

            text_edit = lsp.TextEdit(
                range=lsp.Range(
                    start=lsp.Position(line=context.position.line, character=start),
                    end=lsp.Position(line=context.position.line, character=end),
                ),
                new_text=new_text,
            )

        return lsp.CompletionItem(
            label=new_text,
            kind=kind,
            insert_text=insert_text,
            filter_text=filter_text,
            text_edit=text_edit,
        )

    def _find_start_char(self, context: server.CompletionContext) -> int:
        matched_text = context.match.group(0)
        idx = matched_text.find("/")

        while True:
            next_idx = matched_text.find("/", idx + 1)
            if next_idx == -1:
                break

            idx = next_idx

        return idx
