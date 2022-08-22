import itertools

import pytest
from pytest_lsp import Client
from pytest_lsp import check

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import role_target_patterns

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


def filepath_trigger_cases(path: str = ""):
    """Expand a path into all roles and directives we wish to test it with."""
    return [
        *role_target_patterns("download", path, include_modifiers=False),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            [*filepath_trigger_cases("/"), *filepath_trigger_cases("/conf")],
            [
                ("index.rst", ROOT_FILES, None),
                ("theorems/pythagoras.rst", ROOT_FILES, None),
            ],
        ),
        *itertools.product(
            filepath_trigger_cases(),
            [
                ("index.rst", ROOT_FILES, None),
                ("theorems/pythagoras.rst", THEOREM_FILES, None),
            ],
        ),
        *itertools.product(
            filepath_trigger_cases("../"),
            [
                ("theorems/pythagoras.rst", ROOT_FILES, None),
                ("index.rst", {"workspace", "conftest.py"}, None),
            ],
        ),
        *itertools.product(
            filepath_trigger_cases("/theorems/"),
            [
                ("index.rst", THEOREM_FILES, None),
                ("theorems/pythagoras.rst", THEOREM_FILES, None),
            ],
        ),
    ],
)
async def test_download_completions(client: Client, text, setup):
    """Ensure that we can offer correct filepath suggestions for the ``:download:``
    role."""

    filepath, expected, unexpected = setup
    test_uri = client.root_uri + f"/{filepath}"

    results = await completion_request(client, test_uri, text)

    items = {item.label for item in results.items}
    expected = expected or set()
    unexpected = unexpected or set()

    assert expected == items & expected
    assert set() == items & unexpected

    check.completion_items(client, results.items)
