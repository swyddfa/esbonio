from __future__ import annotations

import pathlib
from typing import Any

import pytest
from pygls.protocol import default_converter

from esbonio.server import Uri
from esbonio.server.features.project_manager import Project
from esbonio.server.features.sphinx_manager.client_subprocess import (
    SubprocessSphinxClient,
)
from esbonio.sphinx_agent import types


def check_diagnostics(
    expected: dict[Uri, list[types.Diagnostic]],
    actual: dict[Uri, list[dict[str, Any]]],
):
    """Ensure that two sets of diagnostics are equal."""
    converter = default_converter()
    assert set(actual.keys()) == set(expected.keys())

    for k, ex_diags in expected.items():
        actual_diags = [converter.structure(d, types.Diagnostic) for d in actual[k]]

        assert len(ex_diags) == len(actual_diags)

        for actual_diagnostic in actual_diags:
            # Assumes ranges are unique
            matches = [e for e in ex_diags if e.range == actual_diagnostic.range]
            assert len(matches) == 1

            expected_diagnostic = matches[0]
            assert actual_diagnostic.range == expected_diagnostic.range
            assert actual_diagnostic.severity == expected_diagnostic.severity
            assert actual_diagnostic.message.startswith(expected_diagnostic.message)


@pytest.mark.asyncio
async def test_diagnostics(client: SubprocessSphinxClient, project: Project, uri_for):
    """Ensure that the sphinx agent reports diagnostics collected during the build, and
    that they are correctly reset when fixed."""
    rst_diagnostics_uri = uri_for("workspaces/demo/rst/diagnostics.rst")
    myst_diagnostics_uri = uri_for("workspaces/demo/myst/diagnostics.md")
    index_uri = uri_for("workspaces/demo/index.rst")
    conf_uri = uri_for("workspaces/demo/conf.py")

    message = "undefined label: 'not-a-real-reference'"

    expected = {
        index_uri: [
            types.Diagnostic(
                message='Unknown directive type "grid"',
                severity=types.DiagnosticSeverity.Error,
                range=types.Range(
                    start=types.Position(line=13, character=0),
                    end=types.Position(line=14, character=0),
                ),
            )
        ],
        conf_uri: [
            types.Diagnostic(
                message="Could not import extension sphinx_design",
                severity=types.DiagnosticSeverity.Error,
                range=types.Range(
                    start=types.Position(line=20, character=4),
                    end=types.Position(line=20, character=19),
                ),
            ),
            types.Diagnostic(
                message="no theme named 'furo' found",
                severity=types.DiagnosticSeverity.Error,
                range=types.Range(
                    start=types.Position(line=42, character=0),
                    end=types.Position(line=42, character=19),
                ),
            ),
        ],
        rst_diagnostics_uri: [
            types.Diagnostic(
                message=message,
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=5, character=0),
                    end=types.Position(line=6, character=0),
                ),
            ),
        ],
        myst_diagnostics_uri: [
            types.Diagnostic(
                message=message,
                severity=types.DiagnosticSeverity.Warning,
                range=types.Range(
                    start=types.Position(line=4, character=0),
                    end=types.Position(line=5, character=0),
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

    fixed_expected = expected.copy()
    del fixed_expected[rst_diagnostics_uri]
    check_diagnostics(fixed_expected, actual)

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
