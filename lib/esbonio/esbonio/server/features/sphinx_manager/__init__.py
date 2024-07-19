from __future__ import annotations

from esbonio.server import EsbonioLanguageServer
from esbonio.server.features.project_manager import ProjectManager

from .client import ClientState
from .client import SphinxClient
from .client_subprocess import make_subprocess_sphinx_client
from .config import SphinxConfig
from .manager import SphinxManager

__all__ = [
    "ClientState",
    "SphinxClient",
    "SphinxConfig",
    "SphinxManager",
]


def esbonio_setup(server: EsbonioLanguageServer, project_manager: ProjectManager):
    manager = SphinxManager(make_subprocess_sphinx_client, project_manager, server)
    server.add_feature(manager)

    @server.command("esbonio.sphinx.restart")
    async def restart_client(ls: EsbonioLanguageServer, params, *args):
        ls.logger.debug("esbonio.sphinx.restart: %s", params)

        for item in params:
            if item is None:
                continue

            await manager.restart_client(item["id"])
