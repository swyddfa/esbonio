from functools import partial

from lsprotocol import types

from esbonio.server import EsbonioLanguageServer
from esbonio.server.features.project_manager import ProjectManager
from esbonio.server.features.sphinx_manager import SphinxClient
from esbonio.server.features.sphinx_manager import SphinxManager


async def refresh_diagnostics(
    server: EsbonioLanguageServer,
    projects: ProjectManager,
    client: SphinxClient,
    result,
):
    """Refresh sphinx diagnostics."""
    if (project := projects.get_project(client.src_uri)) is None:
        return

    # TODO: Per-client id.
    server.clear_diagnostics("sphinx")

    collection = await project.get_diagnostics()
    for uri, items in collection.items():
        diagnostics = [
            server.converter.structure(item, types.Diagnostic) for item in items
        ]
        server.set_diagnostics("sphinx", uri, diagnostics)

    server.sync_diagnostics()


def esbonio_setup(
    server: EsbonioLanguageServer,
    sphinx_manager: SphinxManager,
    project_manager: ProjectManager,
):
    sphinx_manager.add_listener(
        "build", partial(refresh_diagnostics, server, project_manager)
    )
