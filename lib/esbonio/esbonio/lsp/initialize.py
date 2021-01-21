"""Server initialization logic."""
import inspect
import importlib
import pathlib
from typing import Dict, List

import appdirs
import sphinx.util.console as console

from docutils.parsers.rst import directives
from docutils.parsers.rst import roles
from pygls.types import (
    CompletionItem,
    CompletionItemKind,
    InitializeParams,
    InsertTextFormat,
    MessageType,
)
from sphinx.application import Sphinx
from sphinx.domains import Domain

from esbonio.lsp.server import RstLanguageServer


def initialized(rst: RstLanguageServer, params: InitializeParams):
    """Do set up once the initial handshake has been completed."""

    init_sphinx(rst)
    update(rst)


def update(rst: RstLanguageServer):
    """Do everything we need to refresh references etc."""

    if rst.app is None:
        return

    rst.reset_diagnostics()

    rst.app.builder.read()
    rst.targets = discover_targets(rst.app)

    for doc, diagnostics in rst.diagnostics.items():
        rst.publish_diagnostics(doc, diagnostics)


def discover_target_types(rst: RstLanguageServer):
    """Discover all the target types we could complete on.

    This returns a dictionary of the form {'rolename': 'objecttype'} which will allow
    us to determine which kind of completions we should suggest when someone starts
    typing out a role.

    This is unlikely to change much during a session, so it's probably safe to compute
    this once on startup.
    """

    if rst.app is None:
        return

    # TODO: Implement proper domain handling, focus on 'py' and 'std' for now.
    domains = rst.app.env.domains
    py = domains["py"]
    std = domains["std"]

    def make_map(domain: Domain):
        types = {}

        for name, obj in domain.object_types.items():
            for role in obj.roles:
                objs = types.get(role, None)

                if objs is None:
                    objs = []

                objs.append(name)
                types[role] = objs

        return types

    rst.target_types = {**make_map(py), **make_map(std)}


def discover_targets(app: Sphinx) -> Dict[str, List[CompletionItem]]:
    """Discover all the targets we can offer as suggestions.

    This returns a dictionary of the form {'objecttype': [CompletionItems]}

    These are likely to change over the course of an editing session, so this should
    also be called when the client notifies us of a file->save event.
    """

    domains = app.env.domains

    def find_targets(domain: Domain):
        items = {}

        for (name, disp, type_, _, _, _) in domain.get_objects():
            list = items.get(type_, None)

            if list is None:
                list = []

            list.append(completion_from_target(name, disp, type_))
            items[type_] = list

        return items

    # TODO: Implement proper domain handling, focus on 'py' and 'std' for now
    py = find_targets(domains["py"])
    std = find_targets(domains["std"])

    return {**py, **std}


TARGET_KINDS = {
    "attribute": CompletionItemKind.Field,
    "doc": CompletionItemKind.File,
    "class": CompletionItemKind.Class,
    # "const": CompletionItemKind.Value,
    "envvar": CompletionItemKind.Variable,
    "function": CompletionItemKind.Function,
    "method": CompletionItemKind.Method,
    "module": CompletionItemKind.Module,
    "term": CompletionItemKind.Text,
}


def completion_from_target(name, display, type_) -> CompletionItem:
    """Convert a target into a completion item we can return to the client"""

    kind = TARGET_KINDS.get(type_, CompletionItemKind.Reference)
    return CompletionItem(name, kind=kind, detail=str(display), insert_text=name)
