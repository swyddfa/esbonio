"""Auto complete suggestions."""
import re

from pygls.types import CompletionList, CompletionParams, Position
from pygls.workspace import Document

from esbonio.lsp.server import RstLanguageServer

NEW_DIRECTIVE = re.compile(r"^\s*\.\.[ ]*([\w-]+)?$")
NEW_ROLE = re.compile(r".*(?<!:):(?!:)[\w-]*")


def get_line_til_position(doc: Document, position: Position) -> str:
    """Return the line up until the position of the cursor."""

    try:
        line = doc.lines[position.line]
    except IndexError:
        return ""

    return line[: position.character]


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
