"""Server initialization logic."""
import inspect
import importlib
import logging
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

    rst.app = init_sphinx(rst)
    discover_completion_items(rst)
    rst.target_types = discover_target_types(rst.app)
    rst.targets = discover_targets(rst.app)


def discover_completion_items(rst: RstLanguageServer):
    """Discover the "static" completion items.

    "Static" completion items are anything that are not likely to change much during the
    course of an editing session. Currently this includes:

    - roles
    - directives
    """
    # Lookup the directives and roles that have been registered
    dirs = {**directives._directive_registry, **directives._directives}
    rst.directives = {k: completion_from_directive(k, v) for k, v in dirs.items()}

    rst.roles = {
        k: completion_from_role(k, v) for k, v in discover_roles(rst.app).items()
    }

    rst.logger.debug("Discovered %s directives", len(rst.directives))
    rst.logger.debug("Discovered %s roles", len(rst.roles))


def discover_roles(app: Sphinx):
    """Discover roles that we can offer as autocomplete suggestions."""
    # Pull out the roles that are available via docutils.
    local_roles = {
        k: v for k, v in roles._roles.items() if v != roles.unimplemented_role
    }

    role_registry = {
        k: v for k, v in roles._role_registry.items() if v != roles.unimplemented_role
    }

    # Don't forget to include the roles that are stored under Sphinx domains.
    # TODO: Implement proper domain handling, focus on std + python for now.
    domains = app.registry.domains
    std_roles = domains["std"].roles
    py_roles = domains["py"].roles

    return {**local_roles, **role_registry, **py_roles, **std_roles}


def discover_target_types(app: Sphinx):
    """Discover all the target types we could complete on.

    This returns a dictionary of the form {'rolename': 'objecttype'} which will allow
    us to determine which kind of completions we should suggest when someone starts
    typing out a role.

    This is unlikely to change much during a session, so it's probably safe to compute
    this once on startup.
    """

    # TODO: Implement proper domain handling, focus on 'py' and 'std' for now.
    domains = app.env.domains
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

    return {**make_map(py), **make_map(std)}


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
    return CompletionItem(name, kind=kind, detail=display, insert_text=name)


def completion_from_role(name, role) -> CompletionItem:
    """Convert an rst directive to a completion item we can return to the client."""
    return CompletionItem(
        name,
        kind=CompletionItemKind.Function,
        detail="role",
        insert_text="{}:`$0`".format(name),
        insert_text_format=InsertTextFormat.Snippet,
    )


class LogIO:
    def __init__(self):
        self.logger = logging.getLogger("esbonio.sphinx")

    def write(self, line):
        self.logger.info(line)


def init_sphinx(rst: RstLanguageServer) -> Sphinx:
    """Initialise a Sphinx application instance."""
    rst.logger.debug("Workspace root %s", rst.workspace.root_uri)

    root = pathlib.Path(rst.workspace.root_uri.replace("file://", ""))
    candidates = list(root.glob("**/conf.py"))

    if len(candidates) == 0:
        rst.show_message(
            "Unable to find your 'conf.py', features will be limited",
            msg_type=MessageType.Warning,
        )
        return

    src = candidates[0].parent
    build = appdirs.user_cache_dir("esbonio", "swyddfa")
    doctrees = pathlib.Path(build) / "doctrees"

    rst.logger.debug("Config dir %s", src)
    rst.logger.debug("Src dir %s", src)
    rst.logger.debug("Build dir %s", build)
    rst.logger.debug("Doctree dir %s", str(doctrees))

    # Disable color codes in Sphinx's log messages.
    console.nocolor()

    # Create a 'LogIO' object which we use to redirect Sphinx's output to the LSP Client
    log = LogIO()
    app = Sphinx(src, src, build, doctrees, "html", status=log, warning=log)

    # Do a read of all the sources to populate the environment with completion targets
    app.builder.read()
    return app
