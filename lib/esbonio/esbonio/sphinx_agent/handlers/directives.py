from __future__ import annotations

import importlib
import inspect
from typing import Optional

from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives as docutils_directives
from pygments.lexers import get_all_lexers

from .. import types
from ..app import Database
from ..app import Sphinx
from ..util import as_json

DIRECTIVES_TABLE = Database.Table(
    "directives",
    [
        Database.Column(name="name", dtype="TEXT"),
        Database.Column(name="implementation", dtype="TEXT"),
        Database.Column(name="location", dtype="JSON"),
        Database.Column(name="argument_providers", dtype="JSON"),
    ],
)


def get_impl_name(directive: type[Directive]) -> str:
    try:
        return f"{directive.__module__}.{directive.__name__}"
    except AttributeError:
        return f"{directive.__module__}.{directive.__class__.__name__}"


def get_impl_location(impl: type[Directive]) -> Optional[str]:
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

    _add_providers(app, directives)

    app.esbonio.db.ensure_table(DIRECTIVES_TABLE)
    app.esbonio.db.clear_table(DIRECTIVES_TABLE)
    app.esbonio.db.insert_values(
        DIRECTIVES_TABLE, [d.to_db(as_json) for d in directives.values()]
    )


def setup(app: Sphinx):
    app.connect("builder-inited", index_directives, priority=999)


def _add_providers(app: Sphinx, directives: dict[str, types.Directive]):
    """Add provider definitions to built in directive types we know about."""

    lexers_provider = _get_lexers_provider()
    filepath_provider = types.Directive.ArgumentProvider(
        "filepath", {"root": app.srcdir}
    )

    for name in ["code-block", "sourcecode", "highlight"]:
        if (directive := directives.get(name)) is not None:
            directive.argument_providers = [lexers_provider]

    for name in ["image", "figure", "include", "literalinclude"]:
        if (directive := directives.get(name)) is not None:
            directive.argument_providers = [filepath_provider]


def _get_lexers_provider() -> types.Directive.ArgumentProvider:
    """Get the argument provider instance that returns the names of pygments lexers."""

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

    return types.Directive.ArgumentProvider("values", {"values": langs})
