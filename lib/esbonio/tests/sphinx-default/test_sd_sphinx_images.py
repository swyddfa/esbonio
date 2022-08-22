import itertools

import pytest
from pytest_lsp import Client
from pytest_lsp import check

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import directive_argument_patterns

ROOT_FILES = {
    "_static",
    "_templates",
    "theorems",
    "conf.py",
    "index.rst",
    "make.bat",
    "Makefile",
}

THEOREM_FILES = {"index.rst", "pythagoras.rst"}


def completion_trigger_cases(path: str = ""):
    return [
        *directive_argument_patterns("image", path),
        *directive_argument_patterns("figure", path),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            [*completion_trigger_cases("/"), *completion_trigger_cases("/conf")],
            [
                ("index.rst", ROOT_FILES, None),
                ("theorems/pythagoras.rst", ROOT_FILES, None),
            ],
        ),
        *itertools.product(
            completion_trigger_cases(),
            [
                ("index.rst", ROOT_FILES, None),
                ("theorems/pythagoras.rst", THEOREM_FILES, None),
            ],
        ),
        *itertools.product(
            completion_trigger_cases("../"),
            [
                ("theorems/pythagoras.rst", ROOT_FILES, None),
                ("index.rst", {"workspace", "conftest.py"}, None),
            ],
        ),
        *itertools.product(
            completion_trigger_cases("/theorems/"),
            [
                ("index.rst", THEOREM_FILES, None),
                ("theorems/pythagoras.rst", THEOREM_FILES, None),
            ],
        ),
    ],
)
async def test_include_argument_completions(client: Client, text: str, setup):
    """Ensure that we can offer the correct filepath suggestions."""

    filepath, expected, unexpected = setup
    test_uri = client.root_uri + f"/{filepath}"

    results = await completion_request(client, test_uri, text)

    items = {item.label for item in results.items}
    expected = expected or set()
    unexpected = unexpected or set()

    assert expected == items & expected
    assert set() == items & unexpected

    check.completion_items(client, results.items)
