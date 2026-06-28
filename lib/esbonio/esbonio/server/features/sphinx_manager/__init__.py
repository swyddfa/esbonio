from __future__ import annotations

from esbonio.server import EsbonioLanguageServer
from esbonio.server.features.project_manager import ProjectManager

from .client import ClientState
from .client import SphinxClient
from .client import make_sphinx_client
from .config import SphinxConfig
from .config import SubProcess
from .config import register_structure_hooks
from .manager import RestartSphinxParams
from .manager import SphinxManager

__all__ = [
    "ClientState",
    "SphinxClient",
    "SphinxConfig",
    "SphinxManager",
    "SubProcess",
    "register_structure_hooks",
]


def esbonio_setup(server: EsbonioLanguageServer, project_manager: ProjectManager):
    manager = SphinxManager(make_sphinx_client, project_manager, server)
    server.add_feature(manager)

    @server.command("esbonio.sphinx.restart")
    async def restart_client(
        ls: EsbonioLanguageServer, params: RestartSphinxParams, *args
    ):
        ls.logger.debug("esbonio.sphinx.restart: %s", params)
        await manager.restart_client(params.id)
