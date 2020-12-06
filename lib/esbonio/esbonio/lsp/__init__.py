from pygls.features import COMPLETION, INITIALIZED, TEXT_DOCUMENT_DID_SAVE

from pygls.types import CompletionParams, InitializeParams, DidSaveTextDocumentParams

from esbonio.lsp.completion import completions
from esbonio.lsp.initialize import initialized, discover_targets
from esbonio.lsp.server import RstLanguageServer, server


@server.feature(INITIALIZED)
def _(rst: RstLanguageServer, params: InitializeParams):
    return initialized(rst, params)


@server.feature(COMPLETION, trigger_characters=[".", ":", "`"])
def _(rst: RstLanguageServer, params: CompletionParams):
    return completions(rst, params)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def _(rst: RstLanguageServer, params: DidSaveTextDocumentParams):
    """Re-read sources on save so we get the latest completion targets."""
    rst.app.builder.read()
    rst.targets = discover_targets(rst.app)
    return
