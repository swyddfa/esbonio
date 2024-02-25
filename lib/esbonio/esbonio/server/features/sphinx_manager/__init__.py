from __future__ import annotations

from esbonio.server import EsbonioLanguageServer

from .client import ClientState
from .client import SphinxClient
from .client_mock import MockSphinxClient
from .client_mock import mock_sphinx_client_factory
from .client_subprocess import make_subprocess_sphinx_client
from .config import SphinxConfig
from .manager import SphinxManager

__all__ = [
    "ClientState",
    "SphinxClient",
    "SphinxConfig",
    "SphinxManager",
    "MockSphinxClient",
    "mock_sphinx_client_factory",
]


def esbonio_setup(server: EsbonioLanguageServer):
    manager = SphinxManager(make_subprocess_sphinx_client, server)
    server.add_feature(manager)
