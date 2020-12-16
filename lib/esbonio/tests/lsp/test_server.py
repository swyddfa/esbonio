import py.test

from pygls.types import Diagnostic, DiagnosticSeverity, Position, Range

from esbonio.lsp.server import RstLanguageServer


def line(linum: int) -> Range:
    """Helper that returns a range targeting a given line."""
    return Range(Position(linum - 1, 0), Position(linum, 0))


@py.test.mark.parametrize(
    "text,expected",
    [
        ("building [mo]: targets for 0 po files that are out of date", {}),
        (
            "/path/to/file.rst:4: WARNING: toctree contains reference to nonexisting document 'changelog'",
            {
                "/path/to/file.rst": [
                    Diagnostic(
                        line(4),
                        "toctree contains reference to nonexisting document 'changelog'",
                        severity=DiagnosticSeverity.Warning,
                        source="sphinx",
                    )
                ]
            },
        ),
        (
            "/path/to/file.rst:120: ERROR: unable to build docs",
            {
                "/path/to/file.rst": [
                    Diagnostic(
                        line(120),
                        "unable to build docs",
                        severity=DiagnosticSeverity.Error,
                        source="sphinx",
                    )
                ]
            },
        ),
        (
            "/path/to/file.rst:71: WARNING: duplicate label: _setup",
            {
                "/path/to/file.rst": [
                    Diagnostic(
                        line(71),
                        "duplicate label: _setup",
                        severity=DiagnosticSeverity.Warning,
                        source="sphinx",
                    )
                ]
            },
        ),
    ],
)
def test_parse_diagnostics(text, expected):
    """Ensure that the language server can parse errors out of sphinx's output."""

    server = RstLanguageServer()
    server.write(text)

    # Unfortunately, Diagnostic is just a Python class without an __eq__ implementation
    # so we need to take a more manual approach to verifying the expected result.
    assert server.diagnostics.keys() == expected.keys()

    for file in server.diagnostics.keys():

        expect = expected[file]
        actual = server.diagnostics[file]
        assert len(expect) == len(actual)

        for a, b in zip(expect, actual):
            assert a.range == b.range
            assert a.message == b.message
            assert a.severity == b.severity
            assert a.source == b.source

    # Ensure that we rest the diagnostics correctly.
    server.reset_diagnostics()
    assert server.diagnostics == {file: [] for file in expected.keys()}
