import logging
import os
import tempfile
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

from esbonio.lsp import SphinxConfig
from esbonio.lsp.sphinx import DiagnosticList, SphinxManagement


def line(linum: int) -> Range:
    return Range(
        start=Position(line=linum - 1, character=0),
        end=Position(line=linum, character=0),
    )


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
    rst.app.confdir = "/some/folder"
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
            "file:///c%3A/Users/username/Project/file.rst", DiagnosticList([1, 2, 3])
        ),
        mock.call("file:///home/username/Project/file.rst", DiagnosticList([4, 5, 6])),
    ]
    assert publish_diagnostics.call_args_list == expected


class TestCreateApp:
    """Test cases around creating Sphinx application instances."""

    @py.test.fixture()
    def rst(self):

        rst = mock.Mock()
        rst.app = None
        rst.cache_dir = None
        rst.logger = logging.getLogger("esbonio.lsp")

        # Pygls functions / attributes
        rst.workspace = mock.Mock()
        rst.show_message = mock.Mock()

        return rst

    def test_default_case(self, rst, testdata):
        """Ensure that we can successfully create an instance of a Sphinx
        application in a "default" scenario."""

        sphinx_default = testdata("sphinx-default", path_only=True)
        rst.workspace.root_uri = f"file://{sphinx_default}"

        manager = SphinxManagement(rst)
        manager.create_app(SphinxConfig())

        assert rst.app is not None
        assert rst.app.confdir == str(sphinx_default)
        assert rst.app.srcdir == str(sphinx_default)
        assert ".cache/esbonio" in rst.app.outdir
        assert rst.app.doctreedir == os.path.realpath(
            os.path.join(rst.app.outdir, "..", "doctrees")
        )

    def test_missing_conf(self, rst):
        """Ensure that if we cannot find a project's conf.py we notify the user."""

        with tempfile.TemporaryDirectory() as confdir:
            rst.workspace.root_uri = f"file://{confdir}"

            manager = SphinxManagement(rst)
            manager.create_app(SphinxConfig())

            assert rst.app is None

            (args, _) = rst.show_message.call_args
            assert "Unable to find" in args[0]

    def test_conf_dir_option(self, rst, testdata):
        """Ensure that we can override the conf.py discovery mechanism if necessary."""

        sphinx_extensions = testdata("sphinx-extensions", path_only=True)
        data_dir = (sphinx_extensions / "..").resolve()
        rst.workspace.root_uri = f"file://{data_dir}"

        config = SphinxConfig(confDir=str(sphinx_extensions))

        manager = SphinxManagement(rst)
        manager.create_app(config)

        assert rst.app is not None
        assert rst.app.confdir == str(sphinx_extensions)

    def test_conf_dir_pattern(self, rst, testdata):
        """Ensure that we can use 'variables' in our setting of the config dir."""

        sphinx_extensions = testdata("sphinx-extensions", path_only=True)
        data_dir = (sphinx_extensions / "..").resolve()
        rst.workspace.root_uri = f"file://{data_dir}"

        config = SphinxConfig(confDir="${workspaceRoot}/sphinx-extensions")

        manager = SphinxManagement(rst)
        manager.create_app(config)

        assert rst.app is not None
        assert rst.app.confdir == str(sphinx_extensions)

    def test_src_dir_absolute_path(self, rst, testdata):
        """Ensure that we can override the src dir if necessary"""

        sphinx_srcdir = testdata("sphinx-srcdir", path_only=True)
        rst.workspace.root_uri = f"file://{sphinx_srcdir}"

        srcdir = (sphinx_srcdir / "../sphinx-default").resolve()
        config = SphinxConfig(srcDir=str(srcdir))

        manager = SphinxManagement(rst)
        manager.create_app(config)

        assert rst.app is not None
        assert rst.app.confdir == str(sphinx_srcdir)
        assert rst.app.srcdir == str(srcdir)

    def test_src_dir_workspace_root(self, rst, testdata):
        """Ensure that we can override the src dir with a path relative to the
        workspace root."""

        datadir = testdata("sphinx-srcdir", path_only=True).parent
        rst.workspace.root_uri = f"file://{datadir}"

        srcdir = "${workspaceRoot}/sphinx-default"
        confdir = "${workspaceRoot}/sphinx-srcdir"
        config = SphinxConfig(srcDir=srcdir, confDir=confdir)

        manager = SphinxManagement(rst)
        manager.create_app(config)

        assert rst.app is not None
        assert rst.app.confdir == str(datadir / "sphinx-srcdir")
        assert rst.app.srcdir == str(datadir / "sphinx-default")

    def test_src_dir_conf_dir(self, rst, testdata):
        """Ensure that we can override the src dir with a path relative to the
        conf dir."""

        sphinx_srcdir = testdata("sphinx-srcdir", path_only=True)
        rst.workspace.root_uri = f"file://{sphinx_srcdir}"

        srcdir = "${confDir}/../sphinx-default"
        config = SphinxConfig(srcDir=srcdir)

        manager = SphinxManagement(rst)
        manager.create_app(config)

        assert rst.app is not None
        assert rst.app.confdir == str(sphinx_srcdir)
        assert rst.app.srcdir == str((sphinx_srcdir / "../sphinx-default").resolve())

    def test_set_cache_dir(self, rst, testdata):
        """Ensure that we can override the cache dir if necessary"""

        with tempfile.TemporaryDirectory() as build_dir:
            sphinx_default = testdata("sphinx-default", path_only=True)

            rst.workspace.root_uri = f"file://{sphinx_default}"

            manager = SphinxManagement(rst)
            manager.create_app(SphinxConfig(buildDir=build_dir))

            assert rst.app is not None
            assert rst.app.confdir == str(sphinx_default)
            assert rst.app.srcdir == str(sphinx_default)
            assert rst.app.outdir == os.path.join(build_dir, "html")
            assert rst.app.doctreedir == os.path.join(build_dir, "doctrees")

    def test_sphinx_exception(self, rst, testdata):
        """Ensure that we correctly handle the case where creating a Sphinx app throws
        an exception."""

        sphinx_error = testdata("sphinx-error", path_only=True)
        rst.workspace.root_uri = f"file://{sphinx_error}"

        manager = SphinxManagement(rst)
        manager.create_app(SphinxConfig())

        assert rst.app is None

        (_, kwargs) = rst.show_message.call_args
        assert "Unable to initialize Sphinx" in kwargs["message"]
