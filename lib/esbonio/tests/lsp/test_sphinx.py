import logging
import unittest.mock as mock

import py.test

from pygls.lsp.types import (
    Diagnostic,
    DiagnosticSeverity,
    DidSaveTextDocumentParams,
    Position,
    Range,
    TextDocumentIdentifier,
)

from esbonio.lsp.sphinx import DiagnosticList, SphinxManagement, find_conf_py


def line(linum: int) -> Range:
    return Range(
        start=Position(line=linum - 1, character=0),
        end=Position(line=linum, character=0),
    )


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
                        range=line(4),
                        message="toctree contains reference to nonexisting document 'changelog'",
                        severity=DiagnosticSeverity.Warning,
                        source="sphinx",
                    )
                ]
            },
        ),
        (
            "c:\\path\\to\\file.rst:4: WARNING: toctree contains reference to nonexisting document 'changelog'",
            {
                "c:\\path\\to\\file.rst": [
                    Diagnostic(
                        range=line(4),
                        message="toctree contains reference to nonexisting document 'changelog'",
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
                        range=line(120),
                        message="unable to build docs",
                        severity=DiagnosticSeverity.Error,
                        source="sphinx",
                    )
                ]
            },
        ),
        (
            "c:\\path\\to\\file.rst:120: ERROR: unable to build docs",
            {
                "c:\\path\\to\\file.rst": [
                    Diagnostic(
                        range=line(120),
                        message="unable to build docs",
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
                        range=line(71),
                        message="duplicate label: _setup",
                        severity=DiagnosticSeverity.Warning,
                        source="sphinx",
                    )
                ]
            },
        ),
        (
            "c:\\path\\to\\file.rst:71: WARNING: duplicate label: _setup",
            {
                "c:\\path\\to\\file.rst": [
                    Diagnostic(
                        range=line(71),
                        message="duplicate label: _setup",
                        severity=DiagnosticSeverity.Warning,
                        source="sphinx",
                    )
                ]
            },
        ),
        (
            "/path/to/file.rst: WARNING: document isn't included in any toctree",
            {
                "/path/to/file.rst": [
                    Diagnostic(
                        range=line(1),
                        message="document isn't included in any toctree",
                        severity=DiagnosticSeverity.Warning,
                        source="sphinx",
                    )
                ]
            },
        ),
        (
            "c:\\path\\to\\file.rst: WARNING: document isn't included in any toctree",
            {
                "c:\\path\\to\\file.rst": [
                    Diagnostic(
                        range=line(1),
                        message="document isn't included in any toctree",
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

    rst = mock.Mock()
    rst.logger = logging.getLogger("rst")

    file = ""
    management = SphinxManagement(rst)
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
    management.reset_diagnostics(file)
    assert len(management.diagnostics[file]) == 0


def test_report_diagnostics():
    """Ensure that diagnostic, filepaths are correctly transformed into uris."""

    publish_diagnostics = mock.Mock()

    rst = mock.Mock()
    rst.publish_diagnostics = publish_diagnostics

    manager = SphinxManagement(rst)
    manager.diagnostics = {
        "c:\\Users\\username\\Project\\file.rst": DiagnosticList([1, 2, 3]),
        "/home/username/Project/file.rst": DiagnosticList([4, 5, 6]),
    }

    doc = TextDocumentIdentifier(uri="/some/file.rst")
    params = DidSaveTextDocumentParams(text_document=doc, text="")

    manager.reset_diagnostics = mock.Mock()
    manager.save(params)

    expected = [
        mock.call(
            "file:///c:\\Users\\username\\Project\\file.rst", DiagnosticList([1, 2, 3])
        ),
        mock.call("file:///home/username/Project/file.rst", DiagnosticList([4, 5, 6])),
    ]
    assert publish_diagnostics.call_args_list == expected
