import json

import pkg_resources

from esbonio.lsp.directives import Directives
from esbonio.lsp.sphinx import SphinxLanguageServer


def esbonio_setup(rst: SphinxLanguageServer, directives: Directives):
    sphinx_docs = pkg_resources.resource_string("esbonio.lsp.sphinx", "directives.json")
    directives.add_documentation(json.loads(sphinx_docs.decode("utf8")))
