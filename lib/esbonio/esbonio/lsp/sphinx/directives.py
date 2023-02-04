import json

from esbonio.lsp.directives import Directives
from esbonio.lsp.sphinx import SphinxLanguageServer
from esbonio.lsp.util import resources


def esbonio_setup(rst: SphinxLanguageServer, directives: Directives):
    sphinx_docs = resources.read_string("esbonio.lsp.sphinx", "directives.json")
    directives.add_documentation(json.loads(sphinx_docs))
