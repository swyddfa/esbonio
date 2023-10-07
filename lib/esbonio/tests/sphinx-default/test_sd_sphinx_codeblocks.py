import itertools

import pytest
from pytest_lsp import LanguageClient

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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, setup",
    [
        *itertools.product(
            [
                *directive_argument_patterns("code-block"),
                *directive_argument_patterns("highlight"),
            ],
            [({"console", "ng2", "python", "pycon"}, None)],
        )
    ],
)
async def test_codeblock_completions(client: LanguageClient, text: str, setup):
    """Ensure that we can offer correct ``.. code-block::`` suggestions."""

    expected, unexpected = setup
    test_uri = client.root_uri + "/test.rst"

    results = await completion_request(client, test_uri, text)

    items = {item.label for item in results.items}
    expected = expected or set()
    unexpected = unexpected or set()

    assert expected == items & expected
    assert set() == items & unexpected


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
                ("index.rst", ROOT_FILES, None),
                ("theorems/pythagoras.rst", ROOT_FILES, None),
            ],
        ),
        *itertools.product(
            directive_argument_patterns("literalinclude", ""),
            [
                ("index.rst", ROOT_FILES, None),
                ("theorems/pythagoras.rst", THEOREM_FILES, None),
            ],
        ),
        *itertools.product(
            directive_argument_patterns("literalinclude", "../"),
            [
                ("theorems/pythagoras.rst", ROOT_FILES, None),
                ("index.rst", {"workspace", "conftest.py"}, None),
            ],
        ),
        *itertools.product(
            directive_argument_patterns("literalinclude", "/theorems/"),
            [
                ("index.rst", THEOREM_FILES, None),
                ("theorems/pythagoras.rst", THEOREM_FILES, None),
            ],
        ),
    ],
)
async def test_include_argument_completions(client: LanguageClient, text, setup):
    """Ensure that we can offer the correct filepath suggestions."""

    filepath, expected, unexpected = setup
    test_uri = client.root_uri + f"/{filepath}"

    results = await completion_request(client, test_uri, text)

    items = {item.label for item in results.items}
    expected = expected or set()
    unexpected = unexpected or set()

    assert expected == items & expected
    assert set() == items & unexpected
