from __future__ import annotations

import pathlib

from esbonio import server
from esbonio.server import Uri

from .project import Project


class ProjectManager(server.LanguageFeature):
    """Responsible for managing project instances."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.projects: dict[str, Project] = {}
        """Holds active project instances"""

    async def shutdown(self, params: None):
        for project in self.projects.values():
            await project.close()

    def register_project(self, scope: str, dbpath: str | pathlib.Path):
        """Register a project."""
        self.logger.debug("Registered project for scope '%s': '%s'", scope, dbpath)
        self.projects[scope] = Project(dbpath, self.converter)

    def get_project(self, uri: Uri) -> Project | None:
        """Return the project instance for the given uri, if available"""
        scope = self.server.configuration.scope_for(uri)

        if (project := self.projects.get(scope, None)) is None:
            self.logger.debug("No applicable project for uri: %s", uri)
            return None

        return project
