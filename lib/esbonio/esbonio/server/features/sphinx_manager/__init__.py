from __future__ import annotations

from esbonio.server import EsbonioLanguageServer

from .manager import SphinxManager


def esbonio_setup(server: EsbonioLanguageServer):
    manager = SphinxManager(server)
    server.add_feature(manager)
