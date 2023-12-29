import pathlib
from typing import Any
from typing import Dict
from typing import List

import pytest
from pygls.protocol import default_converter

from esbonio.server import Uri
from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)
from esbonio.sphinx_agent import types


def check_diagnostics(
    expected: Dict[Uri, List[types.Diagnostic]],
    actual: Dict[Uri, List[Dict[str, Any]]],
):
    """Ensure that two sets of diagnostics are equal."""
    converter = default_converter()
    assert set(actual.keys()) == set(expected.keys())

    for k, ex_diags in expected.items():
        actual_diags = [converter.structure(d, types.Diagnostic) for d in actual[k]]

        # Order of results is not important
        assert set(actual_diags) == set(ex_diags)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_diagnostics(client: SubprocessSphinxClient, uri_for):
    """Ensure that the sphinx agent reports diagnostics collected during the build, and
    that they are correctly reset when fixed."""
    definitions_uri = uri_for("sphinx-default/workspace/definitions.rst")
    options_uri = uri_for("sphinx-default/workspace/directive_options.rst")

    expected = {
        definitions_uri: [
            types.Diagnostic(
                message="image file not readable: _static/bad.png",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=28, character=0),
                    end=types.Position(line=29, character=0),
                ),
            ),
            types.Diagnostic(
                message="unknown document: '/changelog'",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=13, character=0),
                    end=types.Position(line=14, character=0),
                ),
            ),
        ],
        options_uri: [
            types.Diagnostic(
                message="image file not readable: filename.png",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=1, character=0),
                ),
            ),
            types.Diagnostic(
                message="document isn't included in any toctree",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=1, character=0),
                ),
            ),
        ],
    }

    actual = await client.get_diagnostics()
    check_diagnostics(expected, actual)

    await client.build(
        content_overrides={definitions_uri.fs_path: "My Custom Title\n==============="}
    )

    actual = await client.get_diagnostics()
    check_diagnostics({options_uri: expected[options_uri]}, actual)

    # The original diagnostics should be reported when the issues are re-introduced.
    #
    # Note: We have to "override" the contents of the file with the original text to
    #       trick Sphinx into re-building the file.
    await client.build(
        content_overrides={
            definitions_uri.fs_path: pathlib.Path(definitions_uri).read_text()
        }
    )
    actual = await client.get_diagnostics()
    check_diagnostics(expected, actual)
