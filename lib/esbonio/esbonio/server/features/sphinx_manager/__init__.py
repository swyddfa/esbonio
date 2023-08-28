from __future__ import annotations

from esbonio.server import EsbonioLanguageServer

from .client import SphinxClient
from .client_subprocess import make_subprocess_sphinx_client
from .config import SphinxConfig
from .manager import SphinxManager

__all__ = ["SphinxClient", "SphinxConfig", "SphinxManager"]


def esbonio_setup(server: EsbonioLanguageServer):
    manager = SphinxManager(make_subprocess_sphinx_client, server)
    server.add_feature(manager)
