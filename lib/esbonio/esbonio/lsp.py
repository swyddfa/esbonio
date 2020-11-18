import logging
from typing import Dict, Optional

import docutils.parsers.rst.directives as directives
import docutils.parsers.rst.roles as roles

from pygls.features import COMPLETION, INITIALIZED
from pygls.server import LanguageServer
from pygls.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
)

from sphinx.application import Sphinx


def completion_from_directive(name, directive) -> CompletionItem:
    """Convert an rst directive to a completion item we can return to the client."""
    return CompletionItem(name, kind=CompletionItemKind.Class)


def completion_from_role(name, role) -> CompletionItem:
    """Convert an rst directive to a completion item we can return to the client."""
    return CompletionItem(name, kind=CompletionItemKind.Function)


class RstLanguageServer(LanguageServer):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.app = None
        """Sphinx application instance configured for the current project."""

        self.directives: Optional[Dict[str, CompletionItem]] = None
        """Dictionary holding the directives that have been registered."""

        self.roles: Optional[Dict[str, CompletionItem]] = None
        """Dictionary holding the roles that have been registered."""


server = RstLanguageServer()


@server.feature(INITIALIZED)
def on_initialized(rst: RstLanguageServer, params):
    """Do set up once the initial handshake has been completed."""
    rst.logger.debug(params)
    rst.logger.debug(rst.workspace.root_uri)

    # TODO: Create a Sphinx application instance based on the active project

    # Lookup the directives and roles that have been registered
    dirs = {**directives._directive_registry, **directives._directives}
    rst.directives = {k: completion_from_directive(k, v) for k, v in dirs.items()}

    role_s = {**roles._roles, **roles._role_registry}
    rst.roles = {k: completion_from_role(k, v) for k, v in role_s.items()}


@server.feature(COMPLETION, trigger_characters=["."])
def completions(rst: RstLanguageServer, params: CompletionParams):
    uri = params.textDocument.uri
    pos = params.position

    doc = rst.workspace.get_document(uri)
    line = doc.lines[pos.line]

    return CompletionList(False, [*rst.roles.values(), *rst.directives.values()])
