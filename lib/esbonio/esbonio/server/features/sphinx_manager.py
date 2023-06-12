from __future__ import annotations

import asyncio
import sys
from typing import Callable
from typing import Type

from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import DidCloseTextDocumentParams
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidSaveTextDocumentParams
from pygls.client import Client

from esbonio.server import EsbonioLanguageServer
from esbonio.server import LanguageFeature


class SphinxClient(Client):
    """JSON-RPC client used to drive a Sphinx application instance hosted in
    a separate subprocess."""

    def __init__(self, logger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.alive = True

    async def server_exit(self, server: asyncio.subprocess.Process):
        self.logger.debug(f"Process exited with code: {server.returncode}")
        self.alive = False

        if server.returncode != 0:
            stderr = await server.stderr.read()
            self.logger.debug("Stderr:\n%s", stderr.decode("utf8"))


def make_client(logger):
    client = SphinxClient(logger=logger)

    @client.feature("window/logMessage")
    def on_msg(ls: SphinxClient, params):
        ls.logger.info(params.message)

    return client


class SphinxManager(LanguageFeature):
    """Responsible for managing Sphinx application instances."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = None

    def document_change(self, params: DidChangeTextDocumentParams):
        self.logger.debug("Changed document '%s'", params.text_document.uri)

    def document_close(self, params: DidCloseTextDocumentParams):
        self.logger.debug("Closed document '%s'", params.text_document.uri)

    async def document_open(self, params: DidOpenTextDocumentParams):
        self.logger.debug("Opened document '%s'", params.text_document.uri)
        if self.client is None:
            python = "/var/home/alex/Projects/esbonio/.env/bin/python"
            command = [python, "-m", "esbonio.sphinx_agent"]
            self.logger.debug("Starting client: %s", " ".join(command))
            self.client = make_client(self.logger)

            await self.client.start_io(
                *command,
                env={
                    "PYTHONPATH": "/var/home/alex/Projects/esbonio-beta/code/bundled/lib/"
                },
            )

            if self.client.alive:
                self.logger.debug("Creating app")
                await self.client.protocol.send_request_async(
                    "sphinx/createApp", {"command": ["-M", "dirhtml", ".", "./_build"]}
                )
                self.logger.debug("done.")

    def document_save(self, params: DidSaveTextDocumentParams):
        self.logger.debug("Saved document '%s'", params.text_document.uri)


def esbonio_setup(server: EsbonioLanguageServer):
    manager = SphinxManager(server)
    server.add_feature(manager)
