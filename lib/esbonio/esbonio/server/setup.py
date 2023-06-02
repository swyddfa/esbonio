from __future__ import annotations

import importlib
import json
import typing
from typing import Iterable
from typing import Type

from lsprotocol.types import INITIALIZE
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
    def on_initialize(ls: EsbonioLanguageServer, params: InitializeParams):
        client = params.client_info
        client_capabilities = ls.converter.unstructure(params.capabilities)

        if client is not None:
            ls.logger.info("Language client: %s %s", client.name, client.version)

        ls.logger.debug(
            "Client capabilities:\n%s", json.dumps(client_capabilities, indent=2)
        )

        ls.initialize(params)

    return server


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
