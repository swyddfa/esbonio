import pytest
from lsprotocol import types

from esbonio.cli import esbonio_converter


@pytest.mark.parametrize(
    "data, expected",
    [
        (dict(line=None, character=0), types.Position(line=0, character=0)),
        (dict(line=-1, character=0), types.Position(line=0, character=0)),
        (
            dict(line=int(1e100), character=0),
            types.Position(line=2147483647, character=0),
        ),
        (dict(line=1, character=-2), types.Position(line=1, character=0)),
        (dict(line=1, character=None), types.Position(line=1, character=0)),
        (
            dict(line=1, character=int(1e100)),
            types.Position(line=1, character=2147483647),
        ),
        (
            dict(
                diagnostics=[
                    dict(
                        message="Example message",
                        range=dict(
                            start=dict(line=1, character=0),
                            end=dict(line=1, character=int(1e100)),
                        ),
                    )
                ]
            ),
            types.CodeActionContext(
                diagnostics=[
                    types.Diagnostic(
                        message="Example message",
                        range=types.Range(
                            start=types.Position(line=1, character=0),
                            end=types.Position(line=1, character=2147483647),
                        ),
                    ),
                ],
            ),
        ),
    ],
)
def test_parse_invalid_data(data, expected):
    """Ensure that we can handle invalid data as gracefully as possible."""
    converter = esbonio_converter()
    assert converter.structure(data, type(expected)) == expected
