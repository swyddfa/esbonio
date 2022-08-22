import itertools
from typing import Optional
from typing import Set
from typing import Tuple

import pytest
from pytest_lsp import Client
from pytest_lsp import check

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import role_patterns

EXPECTED = {"doc", "py:func", "py:mod", "ref", "func"}
UNEXPECTED = {"c:func", "c:macro", "restructuredtext-unimplemented-role"}

PY_EXPECTED = {"py:func", "py:mod"}
PY_UNEXPECTED = {"c:func", "c:macro"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            role_patterns(":") + role_patterns(":r") + role_patterns(":ref:"),
            [(EXPECTED, UNEXPECTED)],
        ),
        *itertools.product(
            role_patterns("a:") + role_patterns("figure::"),
            [(None, None)],
        ),
        *itertools.product(
            role_patterns(":py:"),
            [(PY_EXPECTED, PY_UNEXPECTED)],
        ),
        *itertools.product(
            role_patterns(":c:"),
            [(EXPECTED, UNEXPECTED)],
        ),
    ],
)
async def test_role_completions(
    client: Client,
    text: str,
    setup: Tuple[str, Optional[Set[str]], Optional[Set[str]]],
):
    """Ensure that we can offer correct role suggestions.

    This test case is focused on the list of completion items we return for a
    given completion request. This ensures we correctly handle differing sphinx
    configurations and extensions while discovering the available roles.

    Cases are parameterized and the inputs are expected to have the following format::

       ("more info :", ({'expected'}, {'unexpected'}))

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
