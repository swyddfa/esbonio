import itertools

import py.test
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import definition_request
from esbonio.lsp.testing import intersphinx_target_patterns
from esbonio.lsp.testing import role_patterns
from esbonio.lsp.testing import role_target_patterns

C_EXPECTED = {"c:func", "c:macro"}
C_UNEXPECTED = {"ref", "doc", "py:func", "py:mod"}

DEFAULT_EXPECTED = {"doc", "func", "mod", "ref", "c:func"}
DEFAULT_UNEXPECTED = {"py:func", "py:mod", "restructuredtext-unimplemented-role"}

EXT_EXPECTED = {"doc", "py:func", "py:mod", "ref", "func"}
EXT_UNEXPECTED = {"c:func", "c:macro", "restructuredtext-unimplemented-role"}

PY_EXPECTED = {"py:func", "py:mod"}
PY_UNEXPECTED = {"ref", "doc", "c:func", "c:macro"}


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            role_patterns(":") + role_patterns(":r"),
            [
                ("sphinx-default", DEFAULT_EXPECTED, DEFAULT_UNEXPECTED),
                ("sphinx-extensions", EXT_EXPECTED, EXT_UNEXPECTED),
            ],
        ),
        *itertools.product(
            role_patterns(":ref:") + role_patterns("a:") + role_patterns("figure::"),
            [("sphinx-default", None, None), ("sphinx-extensions", None, None)],
        ),
        *itertools.product(
            role_patterns(":py:"),
            [
                ("sphinx-default", None, None),
                ("sphinx-extensions", PY_EXPECTED, PY_UNEXPECTED),
            ],
        ),
        *itertools.product(
            role_patterns(":c:"),
            [
                ("sphinx-default", C_EXPECTED, C_UNEXPECTED),
                ("sphinx-extensions", None, None),
            ],
        ),
    ],
)
async def test_role_completions(client_server, text, setup):
    """Ensure that we can offer correct role suggestions."""

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


WELCOME_LABEL = Location(
    uri="index.rst",
    range=Range(
        start=Position(line=5, character=0),
        end=Position(line=6, character=0),
    ),
)


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "project,path,position,expected",
    [
        ("sphinx-default", "definitions.rst", Position(line=3, character=33), None),
        ("sphinx-default", "definitions.rst", Position(line=5, character=13), None),
        ("sphinx-default", "definitions.rst", Position(line=7, character=33), None),
        ("sphinx-default", "definitions.rst", Position(line=9, character=42), None),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=5, character=33),
            WELCOME_LABEL,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=9, character=35),
            WELCOME_LABEL,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=11, character=28),
            WELCOME_LABEL,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=11, character=35),
            WELCOME_LABEL,
        ),
        (
            "sphinx-default",
            "definitions.rst",
            Position(line=9, character=56),
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
            Position(line=13, character=36),
            Location(
                uri="changelog.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
    ],
)
async def test_role_target_definitions(
    client_server, project, path, position, expected
):
    """Ensure that we can offer the correct definitions for role targets."""

    test = await client_server(project)
    test_uri = test.server.workspace.root_uri + f"/{path}"

    results = await definition_request(test, test_uri, position)

    if expected is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        result = results[0]

        assert result.uri == test.server.workspace.root_uri + f"/{expected.uri}"
        assert result.range == expected.range


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        # Standard domain
        *itertools.product(
            role_target_patterns("doc"),
            [
                (
                    "sphinx-default",
                    {"index", "glossary", "theorems/index", "theorems/pythagoras"},
                    None,
                )
            ],
        ),
        *itertools.product(
            role_target_patterns("ref"),
            [
                (
                    "sphinx-default",
                    {
                        "genindex",
                        "modindex",
                        "pythagoras_theorem",
                        "search",
                        "welcome",
                    },
                    None,
                )
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("ref", "python"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"configparser-objects", "types", "whatsnew-index"},
                ),
                (
                    "sphinx-extensions",
                    {"configparser-objects", "types", "whatsnew-index"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("ref", "sphinx"),
            [
                (
                    "sphinx-default",
                    set(),
                    {
                        "basic-domain-markup",
                        "extension-tutorials-index",
                        "writing-builders",
                    },
                ),
                (
                    "sphinx-extensions",
                    {
                        "basic-domain-markup",
                        "extension-tutorials-index",
                        "writing-builders",
                    },
                    set(),
                ),
            ],
        ),
        # Python Domain
        *itertools.product(
            role_target_patterns("class"),
            [
                ("sphinx-default", {"pythagoras.Triangle"}, None),
                ("sphinx-extensions", {"python", "sphinx"}, {"pythagoras.Triangle"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("func"),
            [
                (
                    "sphinx-default",
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                    None,
                ),
                (
                    "sphinx-extensions",
                    {"sphinx", "python"},
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("func", "python"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"_Py_c_sum", "PyErr_Print", "PyUnicode_Count"},
                ),
                (
                    "sphinx-extensions",
                    {"_Py_c_sum", "PyErr_Print", "PyUnicode_Count"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:func"),
            [
                (
                    "sphinx-default",
                    None,
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
                (
                    "sphinx-extensions",
                    {
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                        "python",
                        "sphinx",
                    },
                    None,
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("py:func", "python"),
            [
                (
                    "sphinx-default",
                    set(),
                    {"abc.abstractmethod", "msvcrt.locking", "types.new_class"},
                ),
                (
                    "sphinx-extensions",
                    {"abc.abstractmethod", "msvcrt.locking", "types.new_class"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("meth"),
            [
                ("sphinx-default", {"pythagoras.Triangle.is_right_angled"}, None),
                (
                    "sphinx-extensions",
                    {"sphinx", "python"},
                    {"pythagoras.Triangle.is_right_angled"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:meth"),
            [
                ("sphinx-default", None, {"pythagoras.Triangle.is_right_angled"}),
                (
                    "sphinx-extensions",
                    {"sphinx", "python", "pythagoras.Triangle.is_right_angled"},
                    None,
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("obj"),
            [
                (
                    "sphinx-default",
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                    None,
                ),
                (
                    "sphinx-extensions",
                    {"sphinx", "python"},
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:obj"),
            [
                (
                    "sphinx-extensions",
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                        "python",
                        "sphinx",
                    },
                    None,
                ),
                (
                    "sphinx-default",
                    None,
                    {
                        "pythagoras",
                        "pythagoras.PI",
                        "pythagoras.UNKNOWN",
                        "pythagoras.Triangle",
                        "pythagoras.Triangle.a",
                        "pythagoras.Triangle.b",
                        "pythagoras.Triangle.c",
                        "pythagoras.Triangle.is_right_angled",
                        "pythagoras.calc_hypotenuse",
                        "pythagoras.calc_side",
                    },
                ),
            ],
        ),
    ],
)
async def test_role_target_completions(client_server, text, setup):
    """Ensure that we can offer correct role target suggestions."""

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
