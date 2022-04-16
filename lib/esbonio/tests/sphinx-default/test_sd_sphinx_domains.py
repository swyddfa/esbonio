import itertools

import pytest
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pytest_lsp import check
from pytest_lsp import Client

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import intersphinx_target_patterns
from esbonio.lsp.testing import role_patterns
from esbonio.lsp.testing import role_target_patterns


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, setup",
    [
        # Standard domain
        *itertools.product(
            role_target_patterns("doc"),
            [
                (
                    {"index", "glossary", "theorems/index", "theorems/pythagoras"},
                    None,
                )
            ],
        ),
        *itertools.product(
            [*role_target_patterns("ref"), *role_target_patterns("ref", "sea")],
            [
                (
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
                    set(),
                    {"configparser-objects", "types", "whatsnew-index"},
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("ref", "sphinx"),
            [
                (
                    set(),
                    {
                        "basic-domain-markup",
                        "extension-tutorials-index",
                        "writing-builders",
                    },
                ),
            ],
        ),
        # Python Domain
        *itertools.product(
            role_target_patterns("class"),
            [
                ({"pythagoras.Triangle"}, None),
            ],
        ),
        *itertools.product(
            role_target_patterns("func"),
            [
                (
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                    None,
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("func", "python"),
            [
                (
                    set(),
                    {"_Py_c_sum", "PyErr_Print", "PyUnicode_Count"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:func"),
            [
                (
                    None,
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("py:func", "python"),
            [
                (
                    set(),
                    {"abc.abstractmethod", "msvcrt.locking", "types.new_class"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("meth"),
            [
                ({"pythagoras.Triangle.is_right_angled"}, None),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:meth"),
            [
                (None, {"pythagoras.Triangle.is_right_angled"}),
            ],
        ),
        *itertools.product(
            role_target_patterns("obj"),
            [
                (
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
            ],
        ),
        *itertools.product(
            role_target_patterns("py:obj"),
            [
                (
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
        *itertools.product(
            role_target_patterns("option"),
            [
                (
                    {
                        "pythag -e",
                        "pythag --exact",
                        "pythag -u",
                        "pythag --unit",
                        "pythag -p",
                        "pythag --precision",
                    },
                    None,
                )
            ],
        ),
        # Default Role
        *itertools.product(role_patterns("`"), [(None, None)]),
        *itertools.product(role_patterns("`some label <"), [(None, None)]),
    ],
)
async def test_role_target_completions(client: Client, text: str, setup):
    """Ensure that we can offer correct role target suggestions.

    This test case is focused on the list of completion items we return for a
    given completion request. This ensures we correctly handle differing sphinx
    configurations and extensions while discovering the available roles.

    Cases are parameterized and the inputs are expected to have the following format::

       (":ref:`", ( {'expected'}, {'unexpected'}))

    where:

    - ``{'expected'}`` is the set of completion item labels you expect to see returned
      from the completion request. Can be ``None`` which will assert that no completions
      are returned.
    - ``{'unexpected'}`` is the set of completion item labels you **do not** expect to
      see returned from the completion request.

    A common pattern where a number of different values for ``text`` should produce the
    same set of results within a given setup, is to make use of
    :func:`python:itertools.product` to generate all combinations of setups.

    Parameters
    ----------
    client:
       The client fixture used to drive the test.
    text:
       The text providing the context of the completion request.
    setup:
       The tuple providing the rest of the setup for the test.
    """

    expected, unexpected = setup

    test_uri = client.root_uri + "/test.rst"

    results = await completion_request(client, test_uri, text)

    items = {item.label for item in results.items}
    expected = expected or set()
    unexpected = unexpected or set()

    assert expected == items & expected
    assert set() == items & unexpected

    check.completion_items(client, results.items)


WELCOME_LABEL = Location(
    uri="index.rst",
    range=Range(
        start=Position(line=5, character=0),
        end=Position(line=6, character=0),
    ),
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,position,expected",
    [
        ("definitions.rst", Position(line=3, character=33), None),
        ("definitions.rst", Position(line=5, character=13), None),
        ("definitions.rst", Position(line=7, character=33), None),
        ("definitions.rst", Position(line=9, character=42), None),
        ("definitions.rst", Position(line=5, character=33), WELCOME_LABEL),
        ("definitions.rst", Position(line=9, character=35), WELCOME_LABEL),
        ("definitions.rst", Position(line=11, character=28), WELCOME_LABEL),
        ("definitions.rst", Position(line=11, character=35), WELCOME_LABEL),
        (
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
        (
            "definitions.rst",
            Position(line=29, character=36),
            Location(
                uri="index.rst",
                range=Range(
                    start=Position(line=18, character=0),
                    end=Position(line=19, character=0),
                ),
            ),
        ),
    ],
)
async def test_role_target_definitions(client: Client, path, position, expected):
    """Ensure that we can offer the correct definitions for role targets."""

    test_uri = client.root_uri + f"/{path}"
    results = await client.definition_request(test_uri, position)

    if expected is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        result = results[0]

        assert result.uri == client.root_uri + f"/{expected.uri}"
        assert result.range == expected.range
