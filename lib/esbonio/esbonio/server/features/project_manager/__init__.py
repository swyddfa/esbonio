from __future__ import annotations

from esbonio.server import EsbonioLanguageServer

from .manager import ProjectManager
from .project import Project

__all__ = [
    "Project",
    "ProjectManager",
]


def esbonio_setup(server: EsbonioLanguageServer):
    manager = ProjectManager(server)
    server.add_feature(manager)
