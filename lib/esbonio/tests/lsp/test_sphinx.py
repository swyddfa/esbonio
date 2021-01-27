import unittest.mock as mock

import py.test

from pygls.types import Diagnostic, DiagnosticSeverity, Position, Range

from esbonio.lsp.sphinx import SphinxManagement, find_conf_py


def line(linum: int) -> Range:
    return Range(Position(linum - 1, 0), Position(linum, 0))


@py.test.mark.parametrize(
    "root,expected,candidates",
    [
        ("/home/user/Project", None, []),
        (
            "/home/user/Project/",
            "/home/user/Project/conf.py",
            ["/home/user/Project/conf.py"],
        ),
        (
            "/home/user/Project",
            "/home/user/Project/conf.py",
            ["/home/user/Project/.tox/conf.py", "/home/user/Project/conf.py"],
        ),
        (
            "/home/user/Project",
            "/home/user/Project/conf.py",
            [
                "/home/user/Project/.env/lib/site-packages/pkg/conf.py",
                "/home/user/Project/conf.py",
            ],
        ),
    ],
)
def test_find_conf_py(root, candidates, expected):
    """Ensure that we can correctly find a project's conf.py"""

    with mock.patch("esbonio.lsp.sphinx.pathlib.Path") as MockPath:
        instance = MockPath.return_value
        instance.glob.return_value = candidates

        conf_py = find_conf_py(f"file://{root}")
        assert conf_py == expected


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
    """Ensure that the language server can parse errors from sphinx's output."""

    management = SphinxManagement(mock.Mock())
    management.write(text)

    # Unfortunately, 'Diagnostic' is just a Python class without an __eq__ implementation
    # so we need to take a more manual approach to verifying the expected result.
    assert management.diagnostics.keys() == expected.keys()

    for file in management.diagnostics.keys():

        expect = expected[file]
        actual = management.diagnostics[file]
        assert len(expect) == len(actual)

        for a, b in zip(expect, actual):
            assert a.range == b.range
            assert a.message == b.message
            assert a.severity == b.severity
            assert a.source == b.source

    # Ensure that can correctly reset diagnostics
    management.reset_diagnostics()
    assert management.diagnostics == {file: [] for file in expected.keys()}
