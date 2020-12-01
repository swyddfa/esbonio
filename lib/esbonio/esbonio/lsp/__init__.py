import inspect
import importlib
import logging
import pathlib
import re

import appdirs
import docutils.parsers.rst.directives as directives
import docutils.parsers.rst.roles as roles

from pygls.features import COMPLETION, INITIALIZED
from pygls.server import LanguageServer
from pygls.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    InsertTextFormat,
    MessageType,
    Position,
)
from pygls.workspace import Document

from sphinx.application import Sphinx


def completion_from_directive(name, directive) -> CompletionItem:
    """Convert an rst directive to a completion item we can return to the client."""

    # 'Core' docutils directives are listed as tuples (modulename, ClassName) so we
    # have to go and look them up ourselves.
    if isinstance(directive, tuple):
        mod, cls = directive

        modulename = "docutils.parsers.rst.directives.{}".format(mod)
        module = importlib.import_module(modulename)
        directive = getattr(module, cls)

    documentation = inspect.getdoc(directive)
    return CompletionItem(
        name,
        kind=CompletionItemKind.Class,
        detail="directive",
        documentation=documentation,
        insert_text=" {}:: ".format(name),
    )


def completion_from_role(name, role) -> CompletionItem:
    """Convert an rst directive to a completion item we can return to the client."""
    return CompletionItem(
        name,
        kind=CompletionItemKind.Function,
        detail="role",
        insert_text="{}:`$1`".format(name),
        insert_text_format=InsertTextFormat.Snippet,
    )


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


server = RstLanguageServer()


@server.feature(INITIALIZED)
def on_initialized(rst: RstLanguageServer, params):
    """Do set up once the initial handshake has been completed."""
    rst.logger.debug("Workspace root %s", rst.workspace.root_uri)

    root = pathlib.Path(rst.workspace.root_uri.replace("file://", ""))
    candidates = list(root.glob("**/conf.py"))

    if len(candidates) == 0:
        rst.show_message(
            "Unable to find your 'conf.py', features will be limited",
            msg_type=MessageType.Warning,
        )

    else:
        src = candidates[0].parent
        rst.logger.debug("Found config dir %s", src)
        build = appdirs.user_cache_dir("esbonio", "swyddfa")
        rst.app = Sphinx(src, src, build, build, "html", status=None, warning=None)

    # Lookup the directives and roles that have been registered
    dirs = {**directives._directive_registry, **directives._directives}
    rst.directives = {k: completion_from_directive(k, v) for k, v in dirs.items()}

    role_s = {**roles._roles, **roles._role_registry}
    rst.roles = {k: completion_from_role(k, v) for k, v in role_s.items()}


NEW_DIRECTIVE = re.compile(r"^\s*\.\.[ ]*([\w-]+)?$")
NEW_ROLE = re.compile(r".*(?<!:):(?!:)[\w-]*")


def get_line_til_position(doc: Document, position: Position) -> str:
    """Return the line up until the position of the cursor."""

    try:
        line = doc.lines[position.line]
    except IndexError:
        return ""

    return line[: position.character]


@server.feature(COMPLETION, trigger_characters=[".", ":"])
def completions(rst: RstLanguageServer, params: CompletionParams):
    """Suggest completions based on the current context"""
    uri = params.textDocument.uri
    pos = params.position

    doc = rst.workspace.get_document(uri)
    line = get_line_til_position(doc, pos)
    rst.logger.debug("Line: '{}'".format(line))

    if NEW_DIRECTIVE.match(line):
        candidates = list(rst.directives.values())

    elif NEW_ROLE.match(line):
        candidates = list(rst.roles.values())

    else:
        candidates = []

    return CompletionList(False, candidates)
