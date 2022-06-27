import json

import pkg_resources

from esbonio.lsp.roles import Roles
from esbonio.lsp.rst import RstLanguageServer


def esbonio_setup(rst: RstLanguageServer, roles: Roles):
    docutils_docs = pkg_resources.resource_string("esbonio.lsp.rst", "roles.json")
    roles.add_documentation(json.loads(docutils_docs.decode("utf8")))
