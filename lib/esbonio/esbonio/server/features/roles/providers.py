from __future__ import annotations

import os
import pathlib
import typing

from lsprotocol import types as lsp

from esbonio import server

if typing.TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any


class RoleTargetProvider:
    """Base class for role target providers."""

    def __init__(self, esbonio: server.EsbonioLanguageServer):
        self.converter = esbonio.converter
        self.logger = esbonio.logger.getChild(self.__class__.__name__)

    def hover_target(
        self, context: server.HoverContext, target: str, **kwargs
    ) -> str | None | Coroutine[Any, Any, str | None]:
        """Return the hover text for the given target"""
        return None

    def suggest_targets(
        self, context: server.CompletionContext, **kwargs
    ) -> (
        list[lsp.CompletionItem]
        | None
        | Coroutine[Any, Any, list[lsp.CompletionItem] | None]
    ):
        """Givem a completion context, suggest role targets that may be used."""
        return None

    def find_target_definition(
        self, context: server.DefinitionContext, target: str, **kwargs
    ) -> list[lsp.Location] | None:
        """Find the definition(s) for the given role target.

        Parameters
        ----------
        context
           The context of the definition request

        target
           The target to find the definition for
        """
        return None

    def resolve_target_link(
        self, context: server.DocumentLinkContext, target: str, **kwargs
    ) -> (
        str
        | None
        | tuple[str, str | None]
        | Coroutine[Any, Any, str | None | tuple[str, str | None]]
    ):
        """Resolve a document link request for the given role target.

        Parameters
        ----------
        context
           The context of the document link request

        target
           The target to resolve the link for
        """
        return None


class FilepathProvider(RoleTargetProvider):
    """Target provider for filepaths."""

    def resolve_target_link(
        self,
        context: server.DocumentLinkContext,
        target: str,
        *,
        root: str = "/",
        pattern: str | None = None,
        **kwargs,
    ) -> None | str | tuple[str, str | None]:
        """Given a directive's argument, resolve a link for it if possible.

        Parameters
        ----------
        root
           If the user provides an absolute path, resolve the link relative to this directory.
        """
        path = self._resolve_path(context, target, root)
        uri = server.Uri.for_file(os.path.normpath(path))
        tooltip = "Path exists" if path.exists() else "Path does NOT exist"

        return str(uri), tooltip

    def find_target_definition(
        self,
        context: server.DefinitionContext,
        target: str,
        *,
        root: str = "/",
        pattern: str | None = None,
        **kwargs,
    ) -> list[lsp.Location] | None:
        path = self._resolve_path(context, target, root)
        uri = server.Uri.for_file(os.path.normpath(path))

        if not uri:
            return None

        return [
            lsp.Location(
                uri=str(uri),
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=1, character=0),
                ),
            )
        ]

    def suggest_targets(
        self,
        context: server.CompletionContext,
        *,
        root: str = "/",
        pattern: str | None = None,
        **kwargs,
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
        uri = context.uri
        cwd = pathlib.Path(uri).parent

        if (partial := context.match.group("label")) and partial.startswith("/"):
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

        # TODO: Mkae this work
        # if (start := self._find_start_char(context)) == -1:
        #     insert_text = new_text
        #     filter_text = None
        #     text_edit = None
        # else:
        #     start += 1
        #     _, end = context.match.span()
        #     prefix = context.match.group(0)[start:end]

        #     self.logger.debug(f"{context.match.group(0)}, {start=}, {end=}, {prefix=}")

        #     insert_text = None
        #     filter_text = f"{prefix}{new_text}"  # Needed so VSCode will actually show the results.

        #     text_edit = lsp.TextEdit(
        #         range=lsp.Range(
        #             start=lsp.Position(line=context.position.line, character=start),
        #             end=lsp.Position(line=context.position.line, character=end),
        #         ),
        #         new_text=new_text,
        #     )

        return lsp.CompletionItem(
            label=new_text,
            kind=kind,
            # insert_text=insert_text,
            # filter_text=filter_text,
            # text_edit=text_edit,
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

    def _resolve_path(
        self, context: server.UriContext, argument: str, root: str
    ) -> pathlib.Path:
        if argument.startswith("/"):
            # Be sure to remove the leading '/', otherwise `argument` will wipe out the
            # root when concatenated.
            path = pathlib.Path(root, argument[1:])
        else:
            cwd = pathlib.Path(context.uri).parent
            path = cwd / argument

        return path
