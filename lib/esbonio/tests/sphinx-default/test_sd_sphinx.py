import pathlib
import sys
import tempfile
from typing import List

import appdirs
import pygls.uris as uri
import pytest
from pygls import IS_WIN
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DiagnosticSeverity
from pygls.lsp.types import DocumentLink
from pygls.lsp.types import MessageType
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pytest_lsp import check
from pytest_lsp import Client
from pytest_lsp import ClientServerConfig
from pytest_lsp import make_client_server
from pytest_lsp import make_test_client

from esbonio.lsp import ESBONIO_SERVER_CONFIGURATION
from esbonio.lsp import ESBONIO_SERVER_PREVIEW
from esbonio.lsp.rst import ServerConfig
from esbonio.lsp.sphinx import InitializationOptions
from esbonio.lsp.sphinx import SphinxConfig
from esbonio.lsp.testing import sphinx_version


class SphinxInfo(SphinxConfig):

    command: List[str]
    """The equivalent ``sphinx-build`` command"""

    version: str
    """Sphinx's version number."""


def make_esbonio_client(*args, **kwargs):
    client = make_test_client(*args, **kwargs)

    @client.feature("esbonio/buildStart")
    def _(*args, **kwargs):
        ...

    @client.feature("esbonio/buildComplete")
    def _(*args, **kwargs):
        ...

    return client


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "uri,expected",
    [
        (
            "/definitions.rst",
            [
                DocumentLink(
                    target="${ROOT}/theorems/pythagoras.rst",
                    range=Range(
                        start=Position(line=21, character=20),
                        end=Position(line=21, character=44),
                    ),
                ),
                DocumentLink(
                    target="${ROOT}/index.rst",
                    range=Range(
                        start=Position(line=23, character=20),
                        end=Position(line=23, character=42),
                    ),
                ),
                DocumentLink(
                    target="${ROOT}/_static/vscode-screenshot.png",
                    range=Range(
                        start=Position(line=25, character=11),
                        end=Position(line=25, character=41),
                    ),
                ),
                DocumentLink(
                    target="${ROOT}/glossary.rst",
                    range=Range(
                        start=Position(line=31, character=14),
                        end=Position(line=31, character=23),
                    ),
                ),
            ],
        )
    ],
)
async def test_document_links(client: Client, uri: str, expected: List[DocumentLink]):
    """Ensure that we handle ``textDocument/documentLink`` requests correctly."""

    test_uri = client.root_uri + uri
    links = await client.document_link_request(test_uri)

    assert len(links) == len(expected)

    for expected, actual in zip(expected, links):
        assert expected.range == actual.range

        target = expected.target.replace("${ROOT}", client.root_uri)
        assert target == actual.target
        assert expected.tooltip == actual.tooltip

    check.document_links(client, links)


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@pytest.mark.parametrize(
    "command, path, options, expected",
    [
        (  # Ensure the defaults work
            [sys.executable, "-m", "esbonio"],
            "workspace",
            SphinxConfig(),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure the configured entry point works
            ["esbonio"],
            "workspace",
            SphinxConfig(),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can set confDir to be an explicit path.
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(confDir="ROOT/workspace"),
            SphinxConfig(
                confDir="ROOT/workspace",
                srcDir="ROOT/workspace",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir relative to ${workspaceRoot}
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(confDir="${workspaceRoot}/workspace"),
            SphinxConfig(
                confDir="ROOT/workspace",
                srcDir="ROOT/workspace",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir relative to ${workspaceFolder}
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(confDir="${workspaceFolder}/workspace"),
            SphinxConfig(
                confDir="ROOT/workspace",
                srcDir="ROOT/workspace",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir to be exactly ${workspaceRoot}
            [sys.executable, "-m", "esbonio"],
            "workspace",
            SphinxConfig(confDir="${workspaceRoot}"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir to be exactly ${workspaceFolder}
            [sys.executable, "-m", "esbonio"],
            "workspace",
            SphinxConfig(confDir="${workspaceFolder}"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy srcDir to be an exact path
            [sys.executable, "-m", "esbonio"],
            "workspace-src",
            SphinxConfig(srcDir="ROOT/../workspace"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT/../workspace",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specify srcDir relative to ${workspaceRoot}
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(
                confDir="${workspaceRoot}/workspace-src",
                srcDir="${workspaceRoot}/workspace",
            ),
            SphinxConfig(
                confDir="ROOT/workspace-src",
                srcDir="ROOT/workspace",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specify srcDir relative to ${workspaceFolder}
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(
                confDir="${workspaceRoot}/workspace-src",
                srcDir="${workspaceFolder}/workspace",
            ),
            SphinxConfig(
                confDir="ROOT/workspace-src",
                srcDir="ROOT/workspace",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specify srcDir to be exactly ${confDir}
            [sys.executable, "-m", "esbonio"],
            "workspace",
            SphinxConfig(srcDir="${confDir}"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy srcDir to be relative to ${confDir}
            [sys.executable, "-m", "esbonio"],
            "workspace-src",
            SphinxConfig(srcDir="${confDir}/../workspace"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT/../workspace",
                buildDir=appdirs.user_cache_dir("esbonio", "swyddfa"),
                builderName="html",
            ),
        ),
    ],
)
async def test_initialization(command: List[str], path: str, options, expected):
    """Ensure that the server responds correctly to various initialization options."""

    root_path = pathlib.Path(__file__).parent / path
    root_uri = uri.from_fs_path(str(root_path))

    for key, value in options.dict().items():
        if key in {"conf_dir", "src_dir", "build_dir"} and value is not None:
            path = resolve_path(value, root_path)
            setattr(options, key, str(path))

    config = ClientServerConfig(
        server_command=command,
        root_uri=root_uri,
        initialization_options=InitializationOptions(sphinx=options),
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)
    try:
        await test.start()
        await test.client.wait_for_notification("esbonio/buildComplete")

        configuration = await test.client.execute_command_request(
            ESBONIO_SERVER_CONFIGURATION
        )

        assert len(test.client.messages) == 0
        assert not any(
            [log.message.startswith("[app]") for log in test.client.log_messages]
        )

        assert "sphinx" in configuration
        actual = SphinxInfo(**configuration["sphinx"])

        assert actual.version is not None
        assert expected.build_dir in actual.build_dir
        assert actual.builder_name == expected.builder_name

        # This seems hacky, but paths on windows are case insensitive...
        if IS_WIN:
            assert (
                actual.conf_dir.lower()
                == resolve_path(expected.conf_dir, root_path).lower()
            )
            assert (
                actual.src_dir.lower()
                == resolve_path(expected.src_dir, root_path).lower()
            )
        else:
            assert actual.conf_dir == resolve_path(expected.conf_dir, root_path)
            assert actual.src_dir == resolve_path(expected.src_dir, root_path)

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_dir():
    """Ensure that we can set the build_dir to an absolute path."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    with tempfile.TemporaryDirectory() as build_dir:
        config = ClientServerConfig(
            server_command=[sys.executable, "-m", "esbonio"],
            root_uri=root_uri,
            initialization_options=InitializationOptions(
                sphinx=SphinxConfig(buildDir=build_dir)
            ),
            client_factory=make_esbonio_client,
        )

        test = make_client_server(config)
        try:
            await test.start()
            await test.client.wait_for_notification("esbonio/buildComplete")

            configuration = await test.client.execute_command_request(
                ESBONIO_SERVER_CONFIGURATION,
            )

            assert len(test.client.messages) == 0

            assert "sphinx" in configuration
            actual = SphinxInfo(**configuration["sphinx"])

            assert actual.version is not None
            assert actual.builder_name == "html"

            # This seems hacky, but paths on windows are case insensitive...
            if IS_WIN:
                assert actual.conf_dir.lower() == str(root_path).lower()
                assert actual.src_dir.lower() == str(root_path).lower()
                assert (
                    actual.build_dir.lower()
                    == str(pathlib.Path(build_dir, "html")).lower()
                )
            else:
                assert actual.conf_dir == str(root_path)
                assert actual.src_dir == str(root_path)
                assert actual.build_dir == str(pathlib.Path(build_dir, "html"))

        finally:
            await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_dir_workspace_var():
    """Ensure that we can set the build_dir relative to the workspace root."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        initialization_options=InitializationOptions(
            sphinx=SphinxConfig(buildDir="${workspaceRoot}/_build")
        ),
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)

    try:
        await test.start()

        configuration = await test.client.execute_command_request(
            ESBONIO_SERVER_CONFIGURATION,
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = SphinxInfo(**configuration["sphinx"])

        assert actual.version is not None
        assert actual.builder_name == "html"

        # This seems hacky, but paths on windows are case insensitive...
        if IS_WIN:
            assert actual.conf_dir.lower() == str(root_path).lower()
            assert actual.src_dir.lower() == str(root_path).lower()
            assert (
                actual.build_dir.lower()
                == str(pathlib.Path(root_path, "_build", "html")).lower()
            )
        else:
            assert actual.conf_dir == str(root_path)
            assert actual.src_dir == str(root_path)
            assert actual.build_dir == str(pathlib.Path(root_path, "_build", "html"))

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_dir_workspace_folder():
    """Ensure that we can set the build_dir relative to the workspace root."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        initialization_options=InitializationOptions(
            sphinx=SphinxConfig(buildDir="${workspaceFolder}/_build")
        ),
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)

    try:
        await test.start()

        configuration = await test.client.execute_command_request(
            ESBONIO_SERVER_CONFIGURATION,
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = SphinxInfo(**configuration["sphinx"])

        assert actual.version is not None
        assert actual.builder_name == "html"

        # This seems hacky, but paths on windows are case insensitive...
        if IS_WIN:
            assert actual.conf_dir.lower() == str(root_path).lower()
            assert actual.src_dir.lower() == str(root_path).lower()
            assert (
                actual.build_dir.lower()
                == str(pathlib.Path(root_path, "_build", "html")).lower()
            )
        else:
            assert actual.conf_dir == str(root_path)
            assert actual.src_dir == str(root_path)
            assert actual.build_dir == str(pathlib.Path(root_path, "_build", "html"))

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_dir_confdir():
    """Ensure that we can set the build_dir relative to the project's conf dir."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        initialization_options=InitializationOptions(
            sphinx=SphinxConfig(buildDir="${confDir}/../_build")
        ),
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)

    try:
        await test.start()

        configuration = await test.client.execute_command_request(
            ESBONIO_SERVER_CONFIGURATION,
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = SphinxInfo(**configuration["sphinx"])
        expected_dir = pathlib.Path(actual.conf_dir, "..", "_build", "html").resolve()

        assert actual.version is not None
        assert actual.builder_name == "html"

        # This seems hacky, but paths on windows are case insensitive...
        if IS_WIN:
            assert actual.conf_dir.lower() == str(root_path).lower()
            assert actual.src_dir.lower() == str(root_path).lower()
            assert actual.build_dir.lower() == str(expected_dir).lower()
        else:
            assert actual.conf_dir == str(root_path)
            assert actual.src_dir == str(root_path)
            assert actual.build_dir == str(expected_dir)
    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@pytest.mark.skipif(
    sphinx_version(eq=2), reason="Sphinx 2.x does not wrap config errors"
)
async def test_initialization_sphinx_error():
    """Ensure that the user is notified when we Sphinx throws an exception."""

    root_path = pathlib.Path(__file__).parent / "workspace-error"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        client_factory=make_esbonio_client,
        initialization_options=InitializationOptions(
            server=ServerConfig(logLevel="debug")
        ),
    )

    test = make_client_server(config)
    try:
        await test.start()

        configuration = await test.client.execute_command_request(
            ESBONIO_SERVER_CONFIGURATION,
        )

        assert "sphinx" in configuration

        conf_py = root_uri + "/conf.py"
        if IS_WIN:
            conf_py = conf_py.lower()

        diagnostics = test.client.diagnostics[conf_py]
        assert len(diagnostics) == 1

        diagnostic = diagnostics[0]
        assert diagnostic.message == "division by zero"
        assert diagnostic.source == "conf.py"
        assert diagnostic.severity == DiagnosticSeverity.Error
        assert diagnostic.range == Range(
            start=Position(line=47, character=0), end=Position(line=48, character=0)
        )

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_error():
    """Ensure that the user is notified when we can't build the docs."""

    root_path = pathlib.Path(__file__).parent / "workspace-src"
    root_uri = uri.from_fs_path(str(root_path))

    # Depending on the order in which the tests run, there may be an index.rst
    # file hanging around that we have to delete.
    index_rst = root_path / "index.rst"
    if index_rst.exists():
        index_rst.unlink()

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)
    try:
        await test.start()

        configuration = await test.client.execute_command_request(
            ESBONIO_SERVER_CONFIGURATION,
        )

        assert "sphinx" in configuration
        assert configuration["sphinx"]["version"] is not None

        diagnostic = list(test.client.diagnostics.values())[0][0]
        assert "index.rst not found" in diagnostic.message
        assert diagnostic.source == "sphinx-build"
        assert diagnostic.severity == DiagnosticSeverity.Error

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_missing_conf():
    """Ensure that the user is notified when we can't find their 'conf.py'."""

    with tempfile.TemporaryDirectory() as root_dir:
        root_uri = uri.from_fs_path(root_dir)

        config = ClientServerConfig(
            server_command=[sys.executable, "-m", "esbonio"],
            root_uri=root_uri,
            client_factory=make_esbonio_client,
        )

        test = make_client_server(config)

        try:
            await test.start()

            configuration = await test.client.execute_command_request(
                ESBONIO_SERVER_CONFIGURATION,
            )

            assert "sphinx" in configuration

            assert len(test.client.messages) == 1
            message = test.client.messages[0]

            assert message.type == MessageType.Warning.value
            assert message.message.startswith("Unable to find your 'conf.py'")

        finally:
            await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_verbosity():
    """Ensure that the server respects the verbosity setting."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        initialization_options=InitializationOptions(sphinx=SphinxConfig(verbosity=2)),
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)

    try:
        await test.start()

        configuration = await test.client.execute_command_request(
            ESBONIO_SERVER_CONFIGURATION,
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = SphinxInfo(**configuration["sphinx"])

        assert actual.version is not None
        assert actual.verbosity == 2
        assert any(
            [log.message.startswith("[app]") for log in test.client.log_messages]
        )

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@pytest.mark.parametrize(
    "good,bad,expected",
    [
        pytest.param(
            "Example Title\n-------------\n",
            "Example Title\n-----\n",
            Diagnostic(
                source="sphinx",
                message="""\
Title underline too short.

Example Title
-----""",
                severity=DiagnosticSeverity.Warning,
                range=Range(
                    start=Position(line=1, character=0),
                    end=Position(line=2, character=0),
                ),
            ),
            marks=pytest.mark.skip(
                reason="Sphinx seems to have stopped reporting this one?"
            ),
        ),
        (
            ".. image:: ../workspace/_static/vscode-screenshot.png",
            ".. image:: not-an-image.png",
            Diagnostic(
                source="sphinx",
                message="""\
image file not readable: not-an-image.png""",
                severity=DiagnosticSeverity.Warning,
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=1, character=0),
                ),
            ),
        ),
    ],
)
async def test_diagnostics(good, bad, expected):
    """Ensure that we can correctly convert Sphinx errors/warnings into diagnostics.

    This test is quite involved as we have to ensure both the language server and the
    filesystem are in agreement on the contents of the ``sphinx-srcdir/`` directory so
    that both Sphinx and the language server can do their thing.
    """

    # Setup, start with the file in the "good" state.
    workspace_root = pathlib.Path(__file__).parent / "workspace-src"
    test_path = workspace_root / "index.rst"
    test_uri = uri.from_fs_path(str(test_path))

    if IS_WIN:
        test_uri = test_uri.lower()

    with test_path.open("w") as f:
        f.write(good)

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=uri.from_fs_path(str(workspace_root)),
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)

    try:
        await test.start()
        await test.client.wait_for_notification("esbonio/buildComplete")

        test.client.notify_did_open(test_uri, "rst", good)

        # Change the file so that it's in the "bad" state, we should see a diagnostic
        # reporting the issue.

        with test_path.open("w") as f:
            f.write(bad)

        test.client.notify_did_change(test_uri, bad)
        test.client.notify_did_save(test_uri, bad)

        await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
        actual = test.client.diagnostics[test_uri][0]

        assert actual.range == expected.range
        assert actual.severity == expected.severity
        assert actual.message == expected.message
        assert actual.source == expected.source

        with test_path.open("w") as f:
            f.write(good)

        # Undo the changes, we should see the diagnostic be removed.
        test.client.notify_did_change(test_uri, good)
        test.client.notify_did_save(test_uri, good)

        # Ensure that we remove any resolved diagnostics.
        await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
        assert len(test.client.diagnostics[test_uri]) == 0

        test.client.notify_did_close(test_uri)

    # Cleanup
    finally:
        test_path.unlink()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_delete_clears_diagnostics():
    """Ensure that file deletions both trigger a rebuild and clear any existing
    diagnostics.

    This test is quite involved as we have to ensure both the language server and the
    filesystem are in agreement on the contents of the ``workspace-src/`` directory.
    """

    index = """\
Index
-----

.. toctree::

   test
"""
    good = """\
Test
----

There is no image here.

"""

    bad = """\
Test
----

This image does not resolve.

.. figure:: /notfound.png

"""

    diagnostic = Diagnostic(
        source="sphinx",
        message="""\
image file not readable: notfound.png""",
        severity=DiagnosticSeverity.Warning,
        range=Range(
            start=Position(line=6, character=0),
            end=Position(line=7, character=0),
        ),
    )

    # Setup, start with the file in the "good" state.
    workspace_root = pathlib.Path(__file__).parent / "workspace-src"
    test_path = workspace_root / "test.rst"
    index_path = workspace_root / "index.rst"

    with index_path.open("w") as f:
        f.write(index)

    with test_path.open("w") as f:
        f.write(good)

    test_uri = uri.from_fs_path(str(test_path))
    if IS_WIN:
        test_uri = test_uri.lower()

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=uri.from_fs_path(str(workspace_root)),
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)
    try:
        await test.start()
        await test.client.wait_for_notification("esbonio/buildComplete")

        test.client.notify_did_open(test_uri, "rst", good)
        test.client.notify_did_change(test_uri, bad)

        with test_path.open("w") as f:
            f.write(bad)

        test.client.notify_did_save(test_uri, text=bad)

        await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
        actual = test.client.diagnostics[test_uri][0]

        assert actual.range == diagnostic.range
        assert actual.severity == diagnostic.severity
        assert actual.message == diagnostic.message
        assert actual.source == diagnostic.source

        # Delete the file, we should see a rebuild and the diagnostic be removed.
        test_path.unlink()
        await test.client.notify_did_delete_files(test_uri)

        await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
        assert len(test.client.diagnostics[test_uri]) == 0

    finally:

        if test_path.exists():
            test_path.unlink()

        index_path.unlink()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_preview_default():
    """Ensure that the preview command returns a port number and makes a
    ``window/showDocument`` request by default."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)

    try:
        await test.start()

        result = await test.client.execute_command_request(ESBONIO_SERVER_PREVIEW)

        assert "port" in result
        port = result["port"]

        assert len(test.client.messages) == 0
        assert len(test.client.shown_documents) == 1

        params = test.client.shown_documents.pop()
        assert params.uri == f"http://localhost:{port}"
        assert params.external, "Expected 'external' flag to be set"

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_preview_no_show():
    """Ensure that the preview command returns a port number and does not make a
    ``window/showDocument`` request when asked."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)
    try:
        await test.start()

        result = await test.client.execute_command_request(
            ESBONIO_SERVER_PREVIEW, {"show": False}
        )

        assert "port" in result
        assert result["port"] > 0

        assert len(test.client.messages) == 0
        assert len(test.client.shown_documents) == 0

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_preview_multiple_calls():
    """Ensure that multiple calls to the preview command returns the same port number
    i.e. an existing server process is reused."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        client_factory=make_esbonio_client,
    )

    test = make_client_server(config)
    try:
        await test.start()

        result = await test.client.execute_command_request(
            ESBONIO_SERVER_PREVIEW, {"show": False}
        )

        assert "port" in result
        port = result["port"]
        assert port > 0

        assert len(test.client.messages) == 0
        assert len(test.client.shown_documents) == 0

        result = await test.client.execute_command_request(
            ESBONIO_SERVER_PREVIEW, {"show": False}
        )

        assert "port" in result
        assert port == result["port"]

        assert len(test.client.messages) == 0
        assert len(test.client.shown_documents) == 0

    finally:
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@pytest.mark.parametrize("builder", ["epub", "man", "latex"])
async def test_preview_wrong_builder(builder):
    """Ensure that the preview is only started for supported builders."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        server_command=[sys.executable, "-m", "esbonio"],
        root_uri=root_uri,
        client_factory=make_esbonio_client,
        initialization_options=InitializationOptions(
            sphinx=SphinxConfig(builderName=builder)
        ),
    )

    test = make_client_server(config)
    try:
        await test.start()

        result = await test.client.execute_command_request(ESBONIO_SERVER_PREVIEW)

        assert result == {}
        assert len(test.client.messages) == 1

        message = test.client.messages[0]
        assert (
            message.message
            == f"Previews are not currently supported for the '{builder}' builder."
        )

    finally:
        await test.stop()


def resolve_path(value: str, root_path: pathlib.Path) -> str:

    if value.startswith("$"):
        return value

    return str(pathlib.Path(value.replace("ROOT", str(root_path))).resolve())
