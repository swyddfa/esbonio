"""Extra support for roles added by sphinx."""
import json
import os.path
from typing import List
from typing import Optional

import pkg_resources
import pygls.uris as Uri
from pygls.lsp.types import CompletionItem

from esbonio.lsp.roles import Roles
from esbonio.lsp.rst import CompletionContext
from esbonio.lsp.sphinx import SphinxLanguageServer
from esbonio.lsp.util.filepaths import complete_sphinx_filepaths
from esbonio.lsp.util.filepaths import path_to_completion_item


class Downloads:
    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst
        self.logger = rst.logger.getChild(self.__class__.__name__)

    def complete_targets(
        self, context: CompletionContext, name: str, domain: Optional[str]
    ) -> List[CompletionItem]:

        if domain or name != "download":
            return []

        if not self.rst.app:
            return []

        srcdir = self.rst.app.srcdir
        partial = context.match.group("label")
        base = os.path.dirname(Uri.to_fs_path(context.doc.uri))
        items = complete_sphinx_filepaths(srcdir, base, partial)

        return [path_to_completion_item(context, p) for p in items]


def esbonio_setup(rst: SphinxLanguageServer, roles: Roles):
    sphinx_docs = pkg_resources.resource_string("esbonio.lsp.sphinx", "roles.json")
    roles.add_documentation(json.loads(sphinx_docs.decode("utf8")))

    roles.add_target_completion_provider(Downloads(rst))
