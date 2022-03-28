import itertools

import pytest
from pytest_lsp import check
from pytest_lsp import Client

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import directive_argument_patterns

ROOT_FILES = {
    "theorems",
    "conf.py",
    "index.rst",
    "glossary.rst",
    "make.bat",
    "Makefile",
}

THEOREM_FILES = {"index.rst", "pythagoras.rst"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, setup",
    [
        *itertools.product(
            [
                *directive_argument_patterns("literalinclude", "/"),
                *directive_argument_patterns("literalinclude", "/conf"),
            ],
            [
                ("index.rst", ROOT_FILES, {"python", "sphinx"}),
            ],
        ),
    ],
)
async def test_include_argument_completions(client: Client, text, setup):
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
