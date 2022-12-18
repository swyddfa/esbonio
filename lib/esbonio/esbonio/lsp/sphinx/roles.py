"""Extra support for roles added by sphinx."""
import json
import os.path
from typing import Dict, List, Any
from typing import Optional

import pkg_resources
import pygls.uris as Uri
from pygls.lsp.types import CompletionItem

from esbonio.lsp.roles import RoleLanguageFeature, Roles
from esbonio.lsp.rst import CompletionContext
from esbonio.lsp.sphinx import SphinxLanguageServer
from esbonio.lsp.util.filepaths import complete_sphinx_filepaths
from esbonio.lsp.util.filepaths import path_to_completion_item


class SphinxRoles(RoleLanguageFeature):
    def __init__(self, rst: SphinxLanguageServer):
        self.rst = rst

    def get_role_documentation(
        self, role: str, implementation: str
    ) -> Optional[Dict[str, Any]]:
        if not self.rst.app:
            return

        feature = self.rst.get_feature(Roles)
        if not feature:
            return

        # Try with the primary domain.
        primary_domain = self.rst.app.config.primary_domain
        if primary_domain:
            key = f"{primary_domain}:{role}({implementation})"
            documentation = feature._documentation.get(key)
            if documentation:
                return documentation

        # Try with the standard domain.
        key = f"std:{role}({implementation})"
        return feature._documentation.get(key)


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

    roles.add_feature(SphinxRoles(rst))
    roles.add_target_completion_provider(Downloads(rst))
