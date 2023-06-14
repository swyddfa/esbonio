from __future__ import annotations

import asyncio
import typing

from pygls.client import Client

if typing.TYPE_CHECKING:
    from .manager import SphinxManager


class SphinxClient(Client):
    """JSON-RPC client used to drive a Sphinx application instance hosted in
    a separate subprocess."""

    def __init__(self, manager: SphinxManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = manager
        self.logger = manager.logger

    async def server_exit(self, server: asyncio.subprocess.Process):
        self.logger.debug(f"Process exited with code: {server.returncode}")

        if server.returncode != 0:
            stderr = await server.stderr.read()
            self.logger.debug("Stderr:\n%s", stderr.decode("utf8"))


def make_sphinx_client(manager: SphinxManager):
    client = SphinxClient(manager=manager)

    @client.feature("window/logMessage")
    def on_msg(ls: SphinxClient, params):
        ls.manager.server.show_message_log(params.message)

    return client
