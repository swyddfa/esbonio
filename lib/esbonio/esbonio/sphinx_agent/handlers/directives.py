from __future__ import annotations

import importlib
import inspect
import json
import pathlib
import typing

from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives as docutils_directives
from pygments.lexers import get_all_lexers
from sphinx.util.logging import getLogger

from .. import types
from ..app import Database
from ..app import Sphinx
from ..util import as_json

if typing.TYPE_CHECKING:
    from typing import TypedDict

    class DirectiveInfo(TypedDict):
        documentation: str
        source: str
        license: str


DIRECTIVES_TABLE = Database.Table(
    "directives",
    [
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="implementation", dtype="TEXT"),
        Database.Column(name="documentation", dtype="TEXT"),
        Database.Column(name="location", dtype="JSON"),
        Database.Column(name="argument_providers", dtype="JSON"),
    ],
)
logger = getLogger(__name__)


def get_impl_name(directive: type[Directive]) -> str:
    try:
        return f"{directive.__module__}.{directive.__name__}"
    except AttributeError:
        return f"{directive.__module__}.{directive.__class__.__name__}"


def get_impl_location(impl: type[Directive]) -> str | None:
    """Get the implementation location of the given directive"""

    try:
        if (filepath := inspect.getsourcefile(impl)) is None:
            return None

        uri = types.Uri.for_file(filepath).resolve()
        source, line = inspect.getsourcelines(impl)

        location = types.Location(
            uri=str(uri),
            range=types.Range(
                start=types.Position(line=line - 1, character=0),
                end=types.Position(line=line + len(source), character=0),
            ),
        )

        return as_json(location)
    except Exception:
        # TODO: Log the error somewhere..
        return None


def index_directives(app: Sphinx):
    """Index all the directives that are available to this app.

    Note: While it would be ideal to resolve the implementation location of each
    directive here, the ``get_impl_location`` function is too slow causing a noticable
    lag when initializing the sphinx agent.

    Perhaps it's worth investigating adding our own custom events. If we could register
    a handler and do work on an "initial" doctree when it becomes available, then we can
    resolve the location of just the directives that are used, as we see them for the
    first time.
    """

    directives: dict[str, types.Directive] = {}

    # Process the roles registered through Sphinx
    for name, impl, providers in app.esbonio._directives:
        directives[name] = types.Directive(
            name, get_impl_name(impl), argument_providers=providers
        )

    ignored_directives = {"restructuredtext-test-directive"}
    found_directives = {
        **docutils_directives._directive_registry,  # type: ignore[attr-defined]
        **docutils_directives._directives,  # type: ignore[attr-defined]
    }

    for name, directive in found_directives.items():
        if name in ignored_directives or name in directives:
            continue

        # core docutils directives are a (module, Class) reference.
        if isinstance(directive, tuple):
            try:
                mod, cls = directive
                modulename = f"docutils.parsers.rst.directives.{mod}"
                module = importlib.import_module(modulename)

                directive = getattr(module, cls)
            except Exception:
                # TODO: Log the error somewhere...
                directives[name] = types.Directive(name, None, None)
                continue

        directives[name] = types.Directive(name, get_impl_name(directive))

    populate_known_directives(app, directives)

    app.esbonio.db.ensure_table(DIRECTIVES_TABLE)
    app.esbonio.db.clear_table(DIRECTIVES_TABLE)
    app.esbonio.db.insert_values(
        DIRECTIVES_TABLE, [d.to_db(as_json) for d in directives.values()]
    )


def setup(app: Sphinx):
    app.connect("builder-inited", index_directives, priority=999)


def populate_known_directives(app: Sphinx, directives: dict[str, types.Directive]):
    """Add documentation, argument and option provider definitions to the directive
    types we know about."""

    directive_info = _load_directive_info()

    for directive in directives.values():
        key = f"{directive.name}({directive.implementation})"
        if (info := directive_info.get(key)) is None:
            continue

        directive.documentation = render_docs(info)

    # Add additional information that is best determined at runtime.
    _add_lexers_provider_to(directives)
    _add_filepath_provider_to(directives, app)


def _load_directive_info() -> dict[str, DirectiveInfo]:
    """Load the bundled data on known directives."""

    info: dict[str, DirectiveInfo] = {}

    try:
        path = pathlib.Path(__file__).parent / "docutils.json"
        items = json.loads(path.read_text())
        info.update(items.get("directives", {}))
    except Exception:
        logger.exception("Unable to load info on docutils directives.")

    try:
        path = pathlib.Path(__file__).parent / "sphinx.json"
        items = json.loads(path.read_text())
        info.update(items.get("directives", {}))
    except Exception:
        logger.exception("Unable to load info on sphinx directives.")

    return info


def render_docs(info: DirectiveInfo) -> str:
    lines = list(info["documentation"])

    if (source := info.get("source", "")) != "":
        lines.append(f"\n\n[Source]({source})")

    if (link := info.get("license", "")) != "":
        lines.append(f"\n\n[License]({link})")

    return "\n".join(lines)


def _add_lexers_provider_to(directives: dict[str, types.Directive]) -> None:
    """Add an argument provider that returns the names of pygments lexers to the
    relevant directives."""

    langs = []
    for name, labels, files, mimes in get_all_lexers():
        filenames = ", ".join(f"`{f}`" for f in files)
        mimetypes = ", ".join(f"`{m}`" for m in mimes)

        for label in labels:
            langs.append(
                {
                    "label": label,
                    "kind": 21,  # Constant
                    "documentation": {
                        "kind": "markdown",
                        "value": f"### {name}\nFilenames: {filenames}\n\nMIME Types: {mimetypes}",
                    },
                }
            )

    provider = types.Directive.ArgumentProvider("values", {"values": langs})

    for name in ["code-block", "sourcecode", "highlight"]:
        if (directive := directives.get(name)) is not None:
            directive.argument_providers = [provider]


def _add_filepath_provider_to(directives: dict[str, types.Directive], app: Sphinx):
    """Add an argument provider that returns filepaths relative to the given sphinx
    project to the relevant directives."""

    filepath_provider = types.Directive.ArgumentProvider(
        "filepath", {"root": app.srcdir}
    )

    for name in ["image", "figure", "include", "literalinclude"]:
        if (directive := directives.get(name)) is not None:
            directive.argument_providers = [filepath_provider]
