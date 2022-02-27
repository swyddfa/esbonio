import itertools

import py.test

from esbonio.lsp.testing import completion_request
from esbonio.lsp.testing import role_target_patterns


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


def filepath_trigger_cases(path: str = ""):
    """Expand a path into all roles and directives we wish to test it with."""
    return [
        *role_target_patterns("download", path, include_modifiers=False),
    ]


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "text,setup",
    [
        *itertools.product(
            [*filepath_trigger_cases("/"), *filepath_trigger_cases("/conf")],
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
            filepath_trigger_cases(),
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
            filepath_trigger_cases("../"),
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
            filepath_trigger_cases("/theorems/"),
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
async def test_download_completions(client_server, text, setup):
    """Ensure that we can offer correct filepath suggestions for the ``:download:``
    role."""

    project, filepath, expected, unexpected = setup

    test = await client_server(project)
    test_uri = test.server.workspace.root_uri + f"/{filepath}"

    results = await completion_request(test, test_uri, text)

    items = {item.label for item in results.items}
    unexpected = unexpected or set()

    if expected is None:
        assert len(items) == 0
    else:
        assert expected == items & expected
        assert set() == items & unexpected
