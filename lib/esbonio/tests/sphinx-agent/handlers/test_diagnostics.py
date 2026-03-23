from __future__ import annotations

import pathlib
from typing import Any

import pytest
from pygls.protocol import default_converter
from sphinx import version_info as sphinx_version

from esbonio.server import Uri
from esbonio.server.features.project_manager import Project
from esbonio.server.features.sphinx_manager.client import SphinxClient
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

        assert len(ex_diags) == len(actual_diags), (
            f"Expected {len(ex_diags)} diagnostics for {k}, got {len(actual_diags)}"
        )

        for expected_diagnostic in ex_diags:
            # Match by message prefix (diagnostics may be in the same range (line/column))
            matches = [
                a
                for a in actual_diags
                if a.message.startswith(expected_diagnostic.message)
            ]
            assert len(matches) == 1, (
                f"Expected exactly one match for '{expected_diagnostic.message}' in {k}"
            )

            actual_diagnostic = matches[0]
            assert actual_diagnostic.severity == expected_diagnostic.severity
            assert actual_diagnostic.range == expected_diagnostic.range


@pytest.mark.asyncio
async def test_diagnostics(client: SphinxClient, project: Project, uri_for):
    """Ensure that the sphinx agent reports diagnostics collected during the build, and
    that they are correctly reset when fixed."""
    rst_diagnostics_uri = uri_for("workspaces/demo/rst/diagnostics.rst")
    myst_diagnostics_uri = uri_for("workspaces/demo/myst/diagnostics.md")
    index_uri = uri_for("workspaces/demo/index.rst")
    conf_uri = uri_for("workspaces/demo/conf.py")
    python_uri = uri_for("workspaces/demo/rst/domains/python.rst")

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
    conf_diags_v9 = [
        types.Diagnostic(
            message="unknown role name: external+myst:std:ref",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=1, character=0),
            ),
        ),
        types.Diagnostic(
            message="unknown role name: external:std:ref",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=1, character=0),
            ),
        ),
        types.Diagnostic(
            message="unknown role name: external:rst:role",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=1, character=0),
            ),
        ),
        types.Diagnostic(
            message="unknown role name: external+sphinx:rst:dir",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=1, character=0),
            ),
        ),
    ]
    python_diags_v9 = [
        types.Diagnostic(
            message="duplicate object description of counters.pattern,",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=40, character=0),
                end=types.Position(line=41, character=0),
            ),
        ),
        types.Diagnostic(
            message="duplicate object description of counters.pattern.NoMatchesError,",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=42, character=0),
                end=types.Position(line=43, character=0),
            ),
        ),
        types.Diagnostic(
            message="duplicate object description of counters.pattern.count_numbers,",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=71, character=0),
                end=types.Position(line=72, character=0),
            ),
        ),
        types.Diagnostic(
            message="duplicate object description of counters.pattern.PatternCounter.pattern,",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=61, character=0),
                end=types.Position(line=62, character=0),
            ),
        ),
        types.Diagnostic(
            message="duplicate object description of counters.pattern.DEFAULT_PATTERN,",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=46, character=0),
                end=types.Position(line=47, character=0),
            ),
        ),
        types.Diagnostic(
            message="duplicate object description of counters.pattern.PatternCounter.count,",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=66, character=0),
                end=types.Position(line=67, character=0),
            ),
        ),
        types.Diagnostic(
            message="duplicate object description of counters.pattern.PatternCounter.fromstr,",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=57, character=0),
                end=types.Position(line=58, character=0),
            ),
        ),
        types.Diagnostic(
            message="duplicate object description of counters.pattern.PatternCounter,",
            severity=types.DiagnosticSeverity.Warning,
            range=types.Range(
                start=types.Position(line=52, character=0),
                end=types.Position(line=53, character=0),
            ),
        ),
    ]
    if sphinx_version[0] >= 9:
        expected[conf_uri].extend(conf_diags_v9)
        expected.update(
            {
                python_uri: python_diags_v9,
            }
        )

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
