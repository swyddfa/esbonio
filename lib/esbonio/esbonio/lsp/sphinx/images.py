import os.path
import pathlib
from typing import List
from typing import Optional
from typing import Tuple

import pygls.uris as Uri
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.workspace import Document

from esbonio.lsp.directives import Directives
from esbonio.lsp.rst import CompletionContext
from esbonio.lsp.rst import DefinitionContext
from esbonio.lsp.rst import DocumentLinkContext
from esbonio.lsp.sphinx import SphinxLanguageServer
from esbonio.lsp.util.filepaths import complete_sphinx_filepaths
from esbonio.lsp.util.filepaths import path_to_completion_item


class Images:
    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)

    def complete_arguments(
        self, context: CompletionContext, domain: str, name: str
    ) -> List[CompletionItem]:

        if domain or name not in {"figure", "image"}:
            return []

        if not self.rst.app:
            return []

        srcdir = self.rst.app.srcdir
        partial = context.match.group("argument")
        base = os.path.dirname(Uri.to_fs_path(context.doc.uri))
        items = complete_sphinx_filepaths(srcdir, base, partial)

        return [path_to_completion_item(context, p) for p in items]

    def find_definitions(
        self,
        context: DefinitionContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> List[Location]:

        if domain or directive not in {"figure", "image"}:
            return []

        uri = self.resolve_path(context.doc, argument)
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

    def resolve_link(
        self,
        context: DocumentLinkContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> Tuple[Optional[str], Optional[str]]:

        if domain or directive not in {"figure", "image"}:
            return None, None

        if argument.startswith("https://") or argument.startswith("http://"):
            return argument, None

        return self.resolve_path(context.doc, argument), None

    def resolve_path(self, doc: Document, argument: str) -> Optional[str]:

        if argument.startswith("/"):
            if not self.rst.app:
                return None

            basedir = pathlib.Path(self.rst.app.srcdir)

            # Remove the leading '/' otherwise is will wipe out the basedir when
            # concatenated
            argument = argument[1:]

        else:
            basedir = pathlib.Path(Uri.to_fs_path(doc.uri)).parent

        try:
            fullpath = basedir / argument
            fpath = fullpath.resolve()

            if fpath.exists():
                return Uri.from_fs_path(str(fpath))
        except Exception:
            self.logger.debug("Unable to resolve filepath '%s'", fullpath)

        return None


def esbonio_setup(rst: SphinxLanguageServer, directives: Directives):
    images = Images(rst)

    directives.add_argument_definition_provider(images)
    directives.add_argument_completion_provider(images)
    directives.add_argument_link_provider(images)
