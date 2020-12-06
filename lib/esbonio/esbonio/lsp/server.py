"""Our Lanague Server Class Definition."""
import logging
from pygls.server import LanguageServer


class RstLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.app = None
        """Sphinx application instance configured for the current project."""

        self.directives = {}
        """Dictionary holding the directives that have been registered."""

        self.roles = {}
        """Dictionary holding the roles that have been registered."""

        self.targets = {}
        """Dictionary holding objects that may be referenced by a role."""

        self.target_types = {}
        """Dictionary holding role names and the object types they can reference."""


server = RstLanguageServer()
