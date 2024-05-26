from __future__ import annotations

import pathlib
import typing

from esbonio import server
from esbonio.server import Uri

from .project import Project

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import Optional
    from typing import Union


class ProjectManager(server.LanguageFeature):
    """Responsible for managing project instances."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.projects: Dict[str, Project] = {}
        """Holds active project instances"""

    def register_project(self, scope: str, dbpath: Union[str, pathlib.Path]):
        """Register a project."""
        self.logger.debug("Registered project for scope '%s': '%s'", scope, dbpath)
        self.projects[scope] = Project(dbpath, self.converter)

    def get_project(self, uri: Uri) -> Optional[Project]:
        """Return the project instance for the given uri, if available"""
        scope = self.server.configuration.scope_for(uri)

        if (project := self.projects.get(scope, None)) is None:
            self.logger.debug("No applicable project for uri: %s", uri)
            return None

        return project
