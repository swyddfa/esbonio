import itertools

import py.test
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range

from esbonio.lsp.testing import ClientServer
from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import definition_request
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
    "project, path, position, expected",
    [
        (
            "sphinx-default",
            "theorems/pythagoras.rst",
            Position(line=8, character=4),
            None,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=17, character=20),
            None,
        ),
        (
            "sphinx-default",
            "theorems/pythagoras.rst",
            Position(line=8, character=18),
            Location(
                uri="math.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
        (
            "sphinx-default",
            "theorems/pythagoras.rst",
            Position(line=10, character=22),
            Location(
                uri="math.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=21, character=20),
            Location(
                uri="theorems/pythagoras.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=23, character=25),
            Location(
                uri="index.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
    ],
)
async def test_include_definitions(
    client_server,
    project: str,
    path: str,
    position: Position,
    expected: Location,
):
    """Ensure that we can correctly handle ``textDocument/definition`` requests for
    ``include::`` directive arguments."""

    test = await client_server(project)  # type: ClientServer
    test_uri = test.server.workspace.root_uri + f"/{path}"

    results = await definition_request(test, test_uri, position)

    if expected is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        result = results[0]

        assert result.uri == test.server.workspace.root_uri + f"/{expected.uri}"
        assert result.range == expected.range


def completion_trigger_cases(path: str = ""):
    return [
        *directive_argument_patterns("include", path),
        *directive_argument_patterns("literalinclude", path),
    ]


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            [*completion_trigger_cases("/"), *completion_trigger_cases("/conf")],
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
            ],
        ),
        *itertools.product(
            completion_trigger_cases(),
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
            completion_trigger_cases("../"),
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
            completion_trigger_cases("/theorems/"),
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
