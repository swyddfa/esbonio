import json

import pkg_resources

from esbonio.lsp.directives import Directives
from esbonio.lsp.rst import RstLanguageServer


def esbonio_setup(rst: RstLanguageServer, directives: Directives):
    docutils_docs = pkg_resources.resource_string("esbonio.lsp.rst", "directives.json")
    directives.add_documentation(json.loads(docutils_docs.decode("utf8")))
