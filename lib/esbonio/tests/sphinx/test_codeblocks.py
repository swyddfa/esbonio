import itertools

import py.test

from esbonio.lsp.testing import ClientServer
from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import directive_argument_patterns

DEFAULT_ROOT_FILES = {
    "_static",
    "_templates",
    "theorems",
    "conf.py",
    "index.rst",
    "make.bat",
    "Makefile",
}

EXT_ROOT_FILES = {
    "theorems",
    "conf.py",
    "index.rst",
    "glossary.rst",
    "make.bat",
    "Makefile",
}

THEOREM_FILES = {"index.rst", "pythagoras.rst"}


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            [
                *directive_argument_patterns("code-block"),
                *directive_argument_patterns("highlight"),
            ],
            [("sphinx-default", {"console", "ng2", "python", "pycon"}, None)],
        )
    ],
)
async def test_codeblock_completions(client_server, text, setup):
    """Ensure that we can offer correct ``.. code-block::`` suggestions."""

    project, expected, unexpected = setup

    test = await client_server(project)
    test_uri = test.server.workspace.root_uri + "/test.rst"

    results = await completion_request(test, test_uri, text)

    items = {item.label for item in results.items}
    unexpected = unexpected or set()

    if expected is None:
        assert len(items) == 0
    else:
        assert expected == items & expected
        assert set() == items & unexpected


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            [
                *directive_argument_patterns("literalinclude", "/"),
                *directive_argument_patterns("literalinclude", "/conf"),
            ],
            [
                (
                    "sphinx-default",
                    "index.rst",
                    DEFAULT_ROOT_FILES,
                    None,
                ),
                (
                    "sphinx-default",
                    "theorems/pythagoras.rst",
                    DEFAULT_ROOT_FILES,
                    None,
                ),
                (
                    "sphinx-extensions",
                    "index.rst",
                    EXT_ROOT_FILES,
                    {"python", "sphinx"},
                ),
            ],
        ),
        *itertools.product(
            directive_argument_patterns("literalinclude", ""),
            [
                (
                    "sphinx-default",
                    "index.rst",
                    DEFAULT_ROOT_FILES,
                    None,
                ),
                (
                    "sphinx-default",
                    "theorems/pythagoras.rst",
                    THEOREM_FILES,
                    None,
                ),
            ],
        ),
        *itertools.product(
            directive_argument_patterns("literalinclude", "../"),
            [
                (
                    "sphinx-default",
                    "theorems/pythagoras.rst",
                    DEFAULT_ROOT_FILES,
                    None,
                ),
                (
                    "sphinx-default",
                    "index.rst",
                    {"sphinx-default", "sphinx-extensions"},
                    None,
                ),
            ],
        ),
        *itertools.product(
            directive_argument_patterns("literalinclude", "/theorems/"),
            [
                (
                    "sphinx-default",
                    "index.rst",
                    THEOREM_FILES,
                    None,
                ),
                (
                    "sphinx-default",
                    "theorems/pythagoras.rst",
                    THEOREM_FILES,
                    None,
                ),
            ],
        ),
    ],
)
async def test_include_argument_completions(client_server, text, setup):
    """Ensure that we can offer the correct filepath suggestions."""

    project, filepath, expected, unexpected = setup

    test = await client_server(project)  # type: ClientServer
    test_uri = test.server.workspace.root_uri + f"/{filepath}"

    results = await completion_request(test, test_uri, text)

    items = {item.label for item in results.items}
    unexpected = unexpected or set()

    if expected is None:
        assert len(items) == 0
    else:
        assert expected == items & expected
        assert set() == items & unexpected
