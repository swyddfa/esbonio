import pathlib
from typing import Any
from typing import Dict
from typing import List

import pytest
from pygls.protocol import default_converter

from esbonio.server import Uri
from esbonio.server.features.project_manager import Project
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
async def test_diagnostics(client: SubprocessSphinxClient, project: Project, uri_for):
    """Ensure that the sphinx agent reports diagnostics collected during the build, and
    that they are correctly reset when fixed."""
    rst_diagnostics_uri = uri_for("workspaces/demo/rst/diagnostics.rst")
    myst_diagnostics_uri = uri_for("workspaces/demo/myst/diagnostics.md")

    expected = {
        rst_diagnostics_uri: [
            types.Diagnostic(
                message="image file not readable: not-an-image.png",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=5, character=0),
                    end=types.Position(line=6, character=0),
                ),
            ),
        ],
        myst_diagnostics_uri: [
            types.Diagnostic(
                message="image file not readable: not-an-image.png",
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=1, character=0),
                ),
            ),
        ],
    }

    actual = await project.get_diagnostics()
    check_diagnostics(expected, actual)

    await client.build(
        content_overrides={
            str(
                rst_diagnostics_uri
            ): "My Custom Title\n===============\n\nThere are no images here"
        }
    )

    actual = await project.get_diagnostics()
    check_diagnostics({myst_diagnostics_uri: expected[myst_diagnostics_uri]}, actual)

    # The original diagnostics should be reported when the issues are re-introduced.
    #
    # Note: We have to "override" the contents of the file with the original text to
    #       trick Sphinx into re-building the file.
    await client.build(
        content_overrides={
            str(rst_diagnostics_uri): pathlib.Path(rst_diagnostics_uri).read_text()
        }
    )
    actual = await project.get_diagnostics()
    check_diagnostics(expected, actual)
