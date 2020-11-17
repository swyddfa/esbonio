import logging

from pygls.features import COMPLETION, INITIALIZED
from pygls.server import LanguageServer
from pygls.types import CompletionItem, CompletionList, CompletionParams


class RstLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)


server = RstLanguageServer()


@server.feature(INITIALIZED)
def on_initialized(rst: RstLanguageServer, params):
    """Do set up once the initial handshake has been completed."""
    rst.logger.debug(params)
    rst.logger.debug(rst.workspace.root_uri)


@server.feature(COMPLETION, trigger_characters=["."])
def completions(rst: RstLanguageServer, params: CompletionParams):
    uri = params.textDocument.uri
    pos = params.position

    doc = rst.workspace.get_document(uri)
    line = doc.lines[pos.line]

    return CompletionList(
        False,
        [
            CompletionItem('"'),
            CompletionItem("["),
            CompletionItem("]"),
            CompletionItem("{"),
            CompletionItem("}"),
        ],
    )
