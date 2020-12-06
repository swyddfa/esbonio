"""Auto complete suggestions."""
import re

from typing import List

from pygls.types import (
    CompletionList,
    CompletionItem,
    CompletionItemKind,
    CompletionParams,
    Position,
)
from pygls.workspace import Document

from esbonio.lsp.server import RstLanguageServer

# Regular expressions used to determine which completions we should offer.

# This should match someone typing out a new directive e.g. .. code-bl|
DIRECTIVE = re.compile(
    r"""^\s*        # directives may be indented
        \.\.        # they start with an rst comment '..'
        [ ]*        # followed by a space
        ([\w-]+)?$  # with an optional name
        """,
    re.VERBOSE,
)

# This should match someone typing out a new role e.g. :re|
ROLE = re.compile(
    r"""(^|.*[ ])  # roles must be preceeded by a space, or start the line
        :          # roles start with the ':' character
        (?!:)      # make sure the next character is not ':'
        [\w-]*     # match the role name
        $          # ensure pattern only matches incomplete roles
    """,
    re.MULTILINE | re.VERBOSE,
)

# This should match someonw typing out a role target e.g. :ref:`ti|
ROLE_TARGET = re.compile(
    r"""(^|.*[ ])          # roles must be preveeded by a space, or start the line
        :                 # roles start with the ':' character
        (?P<name>[\w-]+)  # capture the role name, suggestions will change based on it
        :                 # the role name ends with a ':'
        `                 # the target begins with a '`'`
    """,
    re.MULTILINE | re.VERBOSE,
)


def completions(rst: RstLanguageServer, params: CompletionParams):
    """Suggest completions based on the current context"""
    uri = params.textDocument.uri
    pos = params.position

    doc = rst.workspace.get_document(uri)
    line = get_line_til_position(doc, pos)

    target_match = ROLE_TARGET.match(line)

    if DIRECTIVE.match(line):
        return CompletionList(False, list(rst.directives.values()))

    if target_match:
        return CompletionList(False, suggest_targets(rst, target_match))

    if ROLE.match(line):
        return CompletionList(False, list(rst.roles.values()))

    return CompletionList(False, [])


def suggest_targets(rst: RstLanguageServer, match) -> List[CompletionItem]:
    """Suggest targets based on the current role."""

    if match is None:
        return []

    # Look up the kind of item we need to suggest.
    name = match.group("name")
    types = rst.target_types.get(name, None)

    if types is None:
        return []

    targets = []
    for type_ in types:
        targets += rst.targets.get(type_, [])

    return targets


def get_line_til_position(doc: Document, position: Position) -> str:
    """Return the line up until the position of the cursor."""

    try:
        line = doc.lines[position.line]
    except IndexError:
        return ""

    return line[: position.character]
