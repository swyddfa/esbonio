import itertools

import pytest
from lsprotocol.types import DefinitionParams
from lsprotocol.types import Location
from lsprotocol.types import Position
from lsprotocol.types import Range
from lsprotocol.types import TextDocumentIdentifier
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
    "path, line, character, expected",
    [
        (
            "theorems/pythagoras.rst",
            8,
            4,
            None,
        ),
        (
            "definitions.rst",
            17,
            20,
            None,
        ),
        (
            "theorems/pythagoras.rst",
            8,
            18,
            Location(
                uri="math.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
        (
            "theorems/pythagoras.rst",
            10,
            22,
            Location(
                uri="math.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
        (
            "definitions.rst",
            21,
            20,
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
            23,
            25,
            Location(
                uri="index.rst",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
        (
            "definitions.rst",
            25,
            25,
            Location(
                uri="_static/vscode-screenshot.png",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
        ("definitions.rst", 27, 25, None),
    ],
)
async def test_include_definitions(
    client: LanguageClient,
    path: str,
    line: int,
    character: int,
    expected: Location,
):
    """Ensure that we can correctly handle ``textDocument/definition`` requests for
    ``include::`` directive arguments."""

    test_uri = client.root_uri + f"/{path}"
    results = await client.text_document_definition_async(
        DefinitionParams(
            text_document=TextDocumentIdentifier(uri=test_uri),
            position=Position(line=line, character=character),
        )
    )

    if expected is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        result = results[0]

        assert result.uri == client.root_uri + f"/{expected.uri}"
        assert result.range == expected.range


def completion_trigger_cases(path: str = ""):
    return [
        *directive_argument_patterns("include", path),
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
