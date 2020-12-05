"""Server initialization logic."""
import inspect
import importlib
import logging
import pathlib

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

from esbonio.lsp.server import RstLanguageServer
from esbonio.lsp.logger import LspHandler


def initialized(rst: RstLanguageServer, params: InitializeParams):
    """Do set up once the initial handshake has been completed."""

    init_sphinx(rst)
    discover_completion_items(rst)


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


class LogIO:
    def __init__(self):
        self.logger = logging.getLogger("esbonio.sphinx")

    def write(self, line):
        self.logger.info(line)


def init_sphinx(rst: RstLanguageServer):
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
    rst.app = Sphinx(src, src, build, doctrees, "html", status=log, warning=log)

    # Do a read of all the sources to populate the environment with completion targets
    rst.app.builder.read()
