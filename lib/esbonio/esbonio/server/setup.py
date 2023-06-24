from __future__ import annotations

import importlib
import inspect
import json
import typing
from typing import Iterable
from typing import Type

from lsprotocol.types import INITIALIZE
from lsprotocol.types import TEXT_DOCUMENT_DID_CHANGE
from lsprotocol.types import TEXT_DOCUMENT_DID_CLOSE
from lsprotocol.types import TEXT_DOCUMENT_DID_OPEN
from lsprotocol.types import TEXT_DOCUMENT_DID_SAVE
from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import DidCloseTextDocumentParams
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidSaveTextDocumentParams
from lsprotocol.types import InitializeParams

if typing.TYPE_CHECKING:
    from .server import EsbonioLanguageServer


def create_language_server(
    server_cls: Type[EsbonioLanguageServer], modules: Iterable[str], *args, **kwargs
) -> EsbonioLanguageServer:
    """Create a new language server instance.

    Parameters
    ----------
    server_cls:
       The class definition to create the server from.
    modules:
       The list of modules that should be loaded.
    args, kwargs:
       Any additional arguments that should be passed to the language server's
       constructor.
    """
    server = server_cls(*args, **kwargs)

    for module in modules:
        _load_module(server, module)

    return _configure_lsp_methods(server)


def _configure_lsp_methods(server: EsbonioLanguageServer) -> EsbonioLanguageServer:
    """Configure method handlers for the portions of the LSP spec we support."""

    @server.feature(INITIALIZE)
    async def on_initialize(ls: EsbonioLanguageServer, params: InitializeParams):
        client = params.client_info
        client_capabilities = ls.converter.unstructure(params.capabilities)

        if client is not None:
            ls.logger.info("Language client: %s %s", client.name, client.version)

        # ls.logger.debug(
        #     "Client capabilities:\n%s", json.dumps(client_capabilities, indent=2)
        # )

        ls.initialize(params)

    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    async def on_document_change(
        ls: EsbonioLanguageServer, params: DidChangeTextDocumentParams
    ):
        await call_features(ls, "document_change", params)

    @server.feature(TEXT_DOCUMENT_DID_CLOSE)
    async def on_document_close(
        ls: EsbonioLanguageServer, params: DidCloseTextDocumentParams
    ):
        await call_features(ls, "document_close", params)

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    async def on_document_open(
        ls: EsbonioLanguageServer, params: DidOpenTextDocumentParams
    ):
        await call_features(ls, "document_open", params)

    @server.feature(TEXT_DOCUMENT_DID_SAVE)
    async def on_document_save(
        ls: EsbonioLanguageServer, params: DidSaveTextDocumentParams
    ):
        await call_features(ls, "document_save", params)

    return server


async def call_features(ls: EsbonioLanguageServer, method: str, *args, **kwargs):
    """Call all features."""

    for cls, feature in ls:
        try:
            impl = getattr(feature, method)

            result = impl(*args, **kwargs)
            if inspect.isawaitable(result):
                await result

        except Exception:
            name = f"{cls.__name__}"
            ls.logger.error("Error in '%s.%s' handler", name, method, exc_info=True)


def _load_module(server: EsbonioLanguageServer, modname: str):
    """Load an extension module by calling its ``esbonio_setup`` function, if it exists."""

    try:
        module = importlib.import_module(modname)
    except ImportError:
        server.logger.error("Unable to import module '%s'", modname, exc_info=True)
        return None

    setup = getattr(module, "esbonio_setup", None)
    if setup is None:
        server.logger.debug(
            "Skipping module '%s', missing 'esbonio_setup' function", modname
        )
        return None

    server.load_extension(modname, setup)
