from functools import partial

from lsprotocol import types

from esbonio.server import EsbonioLanguageServer
from esbonio.server.features.sphinx_manager import SphinxClient
from esbonio.server.features.sphinx_manager import SphinxManager


async def refresh_diagnostics(
    server: EsbonioLanguageServer, client: SphinxClient, result
):
    """Refresh sphinx diagnostics."""
    # TODO: Per-client id.
    server.clear_diagnostics("sphinx")

    collection = await client.get_diagnostics()
    for uri, items in collection.items():
        diagnostics = [
            server.converter.structure(item, types.Diagnostic) for item in items
        ]
        server.set_diagnostics("sphinx", uri, diagnostics)

    server.sync_diagnostics()


def esbonio_setup(server: EsbonioLanguageServer, sphinx_manager: SphinxManager):
    sphinx_manager.add_listener("build", partial(refresh_diagnostics, server))
