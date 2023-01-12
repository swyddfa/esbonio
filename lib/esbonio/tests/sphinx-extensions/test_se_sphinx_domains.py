import itertools

import pytest
from pytest_lsp import LanguageClient
from pytest_lsp import check

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import intersphinx_target_patterns
from esbonio.lsp.testing import role_patterns
from esbonio.lsp.testing import role_target_patterns


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, setup",
    [
        *itertools.product(
            intersphinx_target_patterns("ref", "python"),
            [
                (
                    {"configparser-objects", "types", "whatsnew-index"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("ref", "sphinx"),
            [
                (
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
                (
                    set(),  # c domain has no classes.
                    {"pythagoras.Triangle", "python", "sphinx"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("func"),
            [
                (
                    {"sphinx", "python"},
                    {"pythagoras.calc_hypotenuse", "pythagoras.calc_side"},
                ),
            ],
        ),
        *itertools.product(
            intersphinx_target_patterns("func", "python"),
            [
                (
                    {"_Py_c_sum", "PyErr_Print", "PyUnicode_Count"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:func"),
            [
                (
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
                    {"abc.abstractmethod", "msvcrt.locking", "types.new_class"},
                    set(),
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("meth"),
            [
                (
                    set(),  # c domain has no methods.
                    {"pythagoras.Triangle.is_right_angled", "sphinx", "python"},
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:meth"),
            [
                (
                    {"sphinx", "python", "pythagoras.Triangle.is_right_angled"},
                    None,
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("obj"),
            [
                (
                    set(),  # c domain has no objs
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
                        "sphinx",
                        "python",
                    },
                ),
            ],
        ),
        *itertools.product(
            role_target_patterns("py:obj"),
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
                        "python",
                        "sphinx",
                    },
                    None,
                ),
            ],
        ),
        # Default Role
        *itertools.product(
            role_patterns("`"),
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
                        "python",
                        "sphinx",
                    },
                    None,
                ),
            ],
        ),
        *itertools.product(
            role_patterns("`some label <"),
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
                        "python",
                        "sphinx",
                    },
                    None,
                ),
            ],
        ),
    ],
)
async def test_role_target_completions(client: LanguageClient, text: str, setup):
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
