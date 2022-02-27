import os.path
import typing
from typing import List

import pygls.uris as Uri
from pygls.lsp.types import CompletionItem

from esbonio.lsp.directives import Directives
from esbonio.lsp.rst import CompletionContext
from esbonio.lsp.rst import RstLanguageServer
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


def esbonio_setup(rst: RstLanguageServer):

    name = "esbonio.lsp.directives.Directives"
    directives = rst.get_feature(name)

    if not isinstance(rst, SphinxLanguageServer) or not directives:
        return

    # To keep mypy happy.
    directives = typing.cast(Directives, directives)

    directives.add_argument_completion_provider(Images(rst))
