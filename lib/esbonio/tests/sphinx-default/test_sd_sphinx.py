import pathlib
import sys
import tempfile
from typing import List

import platformdirs
import pygls.uris as uri
import pytest
from lsprotocol.types import ClientCapabilities
from lsprotocol.types import DeleteFilesParams
from lsprotocol.types import Diagnostic
from lsprotocol.types import DiagnosticSeverity
from lsprotocol.types import DidChangeTextDocumentParams
from lsprotocol.types import DidCloseTextDocumentParams
from lsprotocol.types import DidOpenTextDocumentParams
from lsprotocol.types import DidSaveTextDocumentParams
from lsprotocol.types import DocumentLink
from lsprotocol.types import DocumentLinkParams
from lsprotocol.types import ExecuteCommandParams
from lsprotocol.types import FileDelete
from lsprotocol.types import InitializeParams
from lsprotocol.types import MessageType
from lsprotocol.types import Position
from lsprotocol.types import Range
from lsprotocol.types import TextDocumentContentChangeEvent_Type2
from lsprotocol.types import TextDocumentIdentifier
from lsprotocol.types import TextDocumentItem
from lsprotocol.types import VersionedTextDocumentIdentifier
from pygls import IS_WIN
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient
from pytest_lsp import make_client_server
from pytest_lsp import make_test_client

from esbonio.lsp import ESBONIO_SERVER_BUILD
from esbonio.lsp import ESBONIO_SERVER_CONFIGURATION
from esbonio.lsp import ESBONIO_SERVER_PREVIEW
from esbonio.lsp.sphinx import InitializationOptions
from esbonio.lsp.sphinx import SphinxConfig
from esbonio.lsp.sphinx.config import SphinxServerConfig
from esbonio.lsp.testing import sphinx_version


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
async def test_document_links(
    client: LanguageClient, uri: str, expected: List[DocumentLink]
):
    """Ensure that we handle ``textDocument/documentLink`` requests correctly."""

    test_uri = client.root_uri + uri
    links = await client.text_document_document_link_async(
        DocumentLinkParams(text_document=TextDocumentIdentifier(uri=test_uri))
    )

    assert len(links) == len(expected)

    for expected, actual in zip(expected, links):
        assert expected.range == actual.range

        target = expected.target.replace("${ROOT}", client.root_uri)
        assert target == actual.target
        assert expected.tooltip == actual.tooltip


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
                conf_dir="ROOT",
                src_dir="ROOT",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure the configured entry point works
            ["esbonio"],
            "workspace",
            SphinxConfig(),
            SphinxConfig(
                conf_dir="ROOT",
                src_dir="ROOT",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can set confDir to be an explicit path.
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(conf_dir="ROOT/workspace"),
            SphinxConfig(
                conf_dir="ROOT/workspace",
                src_dir="ROOT/workspace",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir relative to ${workspaceRoot}
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(conf_dir="${workspaceRoot}/workspace"),
            SphinxConfig(
                conf_dir="ROOT/workspace",
                src_dir="ROOT/workspace",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir relative to ${workspaceFolder}
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(conf_dir="${workspaceFolder}/workspace"),
            SphinxConfig(
                conf_dir="ROOT/workspace",
                src_dir="ROOT/workspace",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir to be exactly ${workspaceRoot}
            [sys.executable, "-m", "esbonio"],
            "workspace",
            SphinxConfig(conf_dir="${workspaceRoot}"),
            SphinxConfig(
                conf_dir="ROOT",
                src_dir="ROOT",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir to be exactly ${workspaceFolder}
            [sys.executable, "-m", "esbonio"],
            "workspace",
            SphinxConfig(conf_dir="${workspaceFolder}"),
            SphinxConfig(
                conf_dir="ROOT",
                src_dir="ROOT",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specifiy srcDir to be an exact path
            [sys.executable, "-m", "esbonio"],
            "workspace-src",
            SphinxConfig(src_dir="ROOT/../workspace"),
            SphinxConfig(
                conf_dir="ROOT",
                src_dir="ROOT/../workspace",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specify srcDir relative to ${workspaceRoot}
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(
                conf_dir="${workspaceRoot}/workspace-src",
                src_dir="${workspaceRoot}/workspace",
            ),
            SphinxConfig(
                conf_dir="ROOT/workspace-src",
                src_dir="ROOT/workspace",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specify srcDir relative to ${workspaceFolder}
            [sys.executable, "-m", "esbonio"],
            ".",
            SphinxConfig(
                conf_dir="${workspaceRoot}/workspace-src",
                src_dir="${workspaceFolder}/workspace",
            ),
            SphinxConfig(
                conf_dir="ROOT/workspace-src",
                src_dir="ROOT/workspace",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specify srcDir to be exactly ${confDir}
            [sys.executable, "-m", "esbonio"],
            "workspace",
            SphinxConfig(src_dir="${confDir}"),
            SphinxConfig(
                conf_dir="ROOT",
                src_dir="ROOT",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
        (  # Ensure that we can specifiy srcDir to be relative to ${confDir}
            [sys.executable, "-m", "esbonio"],
            "workspace-src",
            SphinxConfig(src_dir="${confDir}/../workspace"),
            SphinxConfig(
                conf_dir="ROOT",
                src_dir="ROOT/../workspace",
                build_dir=platformdirs.user_cache_dir("esbonio", "swyddfa"),
                builder_name="html",
            ),
        ),
    ],
)
async def test_initialization(
    converter, command: List[str], path: str, options, expected
):
    """Ensure that the server responds correctly to various initialization options."""

    root_path = pathlib.Path(__file__).parent / path
    root_uri = uri.from_fs_path(str(root_path))

    for key, value in converter.unstructure(options).items():
        if key in {"confDir", "srcDir", "buildDir"} and value is not None:
            path = resolve_path(value, root_path)
            setattr(options, to_snake_case(key), str(path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=command,
    )

    test = make_client_server(config)
    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(sphinx=options),
            )
        )
        await test.client.wait_for_notification("esbonio/buildComplete")

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        # Test some default behaviours.
        assert len(test.client.messages) == 0
        assert len(test.client.log_messages) > 0
        assert not any(
            [log.message.startswith("[app]") for log in test.client.log_messages]
        )

        assert "sphinx" in configuration
        actual = converter.structure(configuration["sphinx"], SphinxConfig)

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
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_dir(converter):
    """Ensure that we can set the build_dir to an absolute path."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    with tempfile.TemporaryDirectory() as build_dir:
        config = ClientServerConfig(
            client_factory=make_esbonio_client,
            server_command=[sys.executable, "-m", "esbonio"],
        )

        test = make_client_server(config)
        try:
            test.start()
            await test.client.initialize_session(
                InitializeParams(
                    capabilities=ClientCapabilities(),
                    root_uri=root_uri,
                    initialization_options=InitializationOptions(
                        sphinx=SphinxConfig(build_dir=build_dir)
                    ),
                )
            )
            await test.client.wait_for_notification("esbonio/buildComplete")

            configuration = await test.client.workspace_execute_command_async(
                ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
            )

            assert len(test.client.messages) == 0

            assert "sphinx" in configuration
            actual = converter.structure(configuration["sphinx"], SphinxConfig)

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
            await test.client.shutdown_session()
            await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_dir_workspace_var(converter):
    """Ensure that we can set the build_dir relative to the workspace root."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    sphinx=SphinxConfig(build_dir="${workspaceRoot}/_build")
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = converter.structure(configuration["sphinx"], SphinxConfig)

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
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_dir_workspace_folder(converter):
    """Ensure that we can set the build_dir relative to the workspace root."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    sphinx=SphinxConfig(build_dir="${workspaceFolder}/_build")
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = converter.structure(configuration["sphinx"], SphinxConfig)

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
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_build_dir_confdir(converter):
    """Ensure that we can set the build_dir relative to the project's conf dir."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    sphinx=SphinxConfig(build_dir="${confDir}/../_build")
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = converter.structure(configuration["sphinx"], SphinxConfig)
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
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_sphinx_error():
    """Ensure that the user is notified when we Sphinx throws an exception."""

    root_path = pathlib.Path(__file__).parent / "workspace-error"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)
    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(log_level="debug")
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
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
        await test.client.shutdown_session()
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
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)
    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(log_level="debug")
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        assert "sphinx" in configuration
        assert configuration["sphinx"]["version"] is not None

        diagnostic = list(test.client.diagnostics.values())[0][0]
        assert "index.rst not found" in diagnostic.message
        assert diagnostic.source == "sphinx-build"
        assert diagnostic.severity == DiagnosticSeverity.Error

    finally:
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_missing_conf():
    """Ensure that the user is notified when we can't find their 'conf.py'."""

    with tempfile.TemporaryDirectory() as root_dir:
        root_uri = uri.from_fs_path(root_dir)

        config = ClientServerConfig(
            client_factory=make_esbonio_client,
            server_command=[sys.executable, "-m", "esbonio"],
        )

        test = make_client_server(config)

        try:
            test.start()
            await test.client.initialize_session(
                InitializeParams(
                    capabilities=ClientCapabilities(),
                    root_uri=root_uri,
                    initialization_options=InitializationOptions(
                        server=SphinxServerConfig(log_level="debug")
                    ),
                )
            )

            configuration = await test.client.workspace_execute_command_async(
                ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
            )

            assert "sphinx" in configuration

            assert len(test.client.messages) == 1
            message = test.client.messages[0]

            assert message.type == MessageType.Warning.value
            assert message.message.startswith("Unable to find your 'conf.py'")

        finally:
            await test.client.shutdown_session()
            await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_verbosity(converter):
    """Ensure that the server respects Sphinx's verbosity setting."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    sphinx=SphinxConfig(verbosity=2)
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = converter.structure(configuration["sphinx"], SphinxConfig)

        assert actual.version is not None
        assert actual.verbosity == 2
        assert any(
            [log.message.startswith("[app]") for log in test.client.log_messages]
        )

    finally:
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_hide_sphinx_output(converter):
    """Ensure that the server respects hide sphinx output setting."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(hide_sphinx_output=True)
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        assert len(test.client.messages) == 0

        assert "server" in configuration
        actual = converter.structure(configuration["server"], SphinxServerConfig)

        assert actual.hide_sphinx_output is True
        assert len(test.client.log_messages) == 0

    finally:
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_silent(converter):
    """Ensure that the server respects Sphinx's silent setting."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    sphinx=SphinxConfig(silent=True)
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = converter.structure(configuration["sphinx"], SphinxConfig)

        assert actual.silent is True
        assert len(test.client.log_messages) == 0

    finally:
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_initialization_quiet(converter):
    """Ensure that the server respects Sphinx's quiet setting."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    sphinx=SphinxConfig(quiet=True)
                ),
            )
        )

        configuration = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_CONFIGURATION)
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = converter.structure(configuration["sphinx"], SphinxConfig)

        assert actual.quiet is True
        assert all(
            [
                ("WARNING" in log.message or "Errno" in log.message)
                for log in test.client.log_messages
            ]
        )

    finally:
        await test.client.shutdown_session()
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
        (
            ".. c:function:: int add(int a, int b)",
            ".. c:function:: arg1",
            Diagnostic(
                source="sphinx",
                message="Error in declarator or parameters\nInvalid C declaration: Expected identifier in nested name. [error at 4]\n  arg1\n  ----^",
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
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=uri.from_fs_path(str(workspace_root)),
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(log_level="debug")
                ),
            )
        )

        await test.client.wait_for_notification("esbonio/buildComplete")

        test.client.text_document_did_open(
            DidOpenTextDocumentParams(
                text_document=TextDocumentItem(
                    uri=test_uri, language_id="rst", version=1, text=good
                )
            )
        )

        # Change the file so that it's in the "bad" state, we should see a diagnostic
        # reporting the issue.

        with test_path.open("w") as f:
            f.write(bad)

        test.client.text_document_did_change(
            DidChangeTextDocumentParams(
                text_document=VersionedTextDocumentIdentifier(uri=test_uri, version=2),
                content_changes=[TextDocumentContentChangeEvent_Type2(text=bad)],
            )
        )

        test.client.text_document_did_save(
            DidSaveTextDocumentParams(
                text_document=TextDocumentIdentifier(uri=test_uri), text=bad
            )
        )

        await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
        actual = test.client.diagnostics[test_uri][0]

        assert actual.range == expected.range
        assert actual.severity == expected.severity
        assert actual.message == expected.message
        assert actual.source == expected.source

        with test_path.open("w") as f:
            f.write(good)

        # Undo the changes, we should see the diagnostic removed.
        test.client.text_document_did_change(
            DidChangeTextDocumentParams(
                text_document=VersionedTextDocumentIdentifier(uri=test_uri, version=3),
                content_changes=[TextDocumentContentChangeEvent_Type2(text=good)],
            )
        )

        test.client.text_document_did_save(
            DidSaveTextDocumentParams(
                text_document=TextDocumentIdentifier(uri=test_uri), text=good
            )
        )

        # Ensure that we remove any resolved diagnostics.
        await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
        assert len(test.client.diagnostics[test_uri]) == 0

        test.client.text_document_did_close(
            DidCloseTextDocumentParams(
                text_document=TextDocumentIdentifier(uri=test_uri)
            )
        )

    # Cleanup
    finally:
        test_path.unlink()

        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@pytest.mark.parametrize(
    "good,bad,expected",
    [
        (
            #  good
            """\
.. _example-label:

Title
-----

:ref:`example-label`
""",
            #  bad
            """\
.. _example-label:

Title
-----

:ref:`example`
""",
            Diagnostic(
                source="sphinx",
                message=(
                    "undefined label: 'example'"
                    if sphinx_version(gte=5)
                    else "undefined label: example"
                ),
                severity=DiagnosticSeverity.Warning,
                range=Range(
                    start=Position(line=5, character=0),
                    end=Position(line=6, character=0),
                ),
            ),
        )
    ],
)
async def test_live_build_clears_diagnostics(good, bad, expected):
    """Ensure that when the server does a build that includes unsaved files it still
    correctly clears diagnostics.
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
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=uri.from_fs_path(str(workspace_root)),
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(enable_live_preview=True)
                ),
            )
        )
        await test.client.wait_for_notification("esbonio/buildComplete")

        test.client.text_document_did_open(
            DidOpenTextDocumentParams(
                text_document=TextDocumentItem(
                    uri=test_uri, language_id="rst", version=1, text=good
                )
            )
        )

        # Change the file so that it's in the bad state, we should see a diagnostic
        # reporting the issue.
        # Note: We don't have to update the file on disk since in live preview mode the
        # server should be injecting the latest content into the build.
        test.client.text_document_did_change(
            DidChangeTextDocumentParams(
                text_document=VersionedTextDocumentIdentifier(uri=test_uri, version=2),
                content_changes=[TextDocumentContentChangeEvent_Type2(text=bad)],
            )
        )

        await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_BUILD)
        )

        actual = test.client.diagnostics[test_uri][0]

        assert actual.range == expected.range
        assert actual.severity == expected.severity
        assert actual.message == expected.message
        assert actual.source == expected.source

        # Undo the changes, we should see the diagnostic removed.
        test.client.text_document_did_change(
            DidChangeTextDocumentParams(
                text_document=VersionedTextDocumentIdentifier(uri=test_uri, version=3),
                content_changes=[TextDocumentContentChangeEvent_Type2(text=good)],
            )
        )

        await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_BUILD)
        )

        assert len(test.client.diagnostics[test_uri]) == 0

        test.client.text_document_did_close(
            DidCloseTextDocumentParams(
                text_document=TextDocumentIdentifier(uri=test_uri)
            )
        )

    finally:
        test_path.unlink()

        await test.client.shutdown_session()
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
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)
    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=uri.from_fs_path(str(workspace_root)),
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(log_level="debug")
                ),
            )
        )
        await test.client.wait_for_notification("esbonio/buildComplete")

        test.client.text_document_did_open(
            DidOpenTextDocumentParams(
                text_document=TextDocumentItem(
                    uri=test_uri, language_id="rst", version=1, text=good
                )
            )
        )

        # Change the file so that it's in the bad state, we should see a diagnostic
        # reporting the issue.
        # Note: We don't have to update the file on disk since in live preview mode the
        # server should be injecting the latest content into the build.
        test.client.text_document_did_change(
            DidChangeTextDocumentParams(
                text_document=VersionedTextDocumentIdentifier(uri=test_uri, version=2),
                content_changes=[TextDocumentContentChangeEvent_Type2(text=bad)],
            )
        )

        with test_path.open("w") as f:
            f.write(bad)

        test.client.text_document_did_save(
            DidSaveTextDocumentParams(
                text_document=TextDocumentIdentifier(uri=test_uri), text=bad
            )
        )

        await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
        actual = test.client.diagnostics[test_uri][0]

        assert actual.range == diagnostic.range
        assert actual.severity == diagnostic.severity
        assert actual.message == diagnostic.message
        assert actual.source == diagnostic.source

        # Delete the file, we should see a rebuild and the diagnostic be removed.
        test_path.unlink()
        test.client.workspace_did_delete_files(
            DeleteFilesParams(files=[FileDelete(uri=test_uri)])
        )

        await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
        assert len(test.client.diagnostics[test_uri]) == 0

    finally:
        if test_path.exists():
            test_path.unlink()

        index_path.unlink()

        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_preview_default():
    """Ensure that the preview command returns a port number and makes a
    ``window/showDocument`` request by default."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)

    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(log_level="debug")
                ),
            )
        )

        result = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_PREVIEW)
        )

        assert "port" in result
        port = result["port"]

        assert len(test.client.messages) == 0
        assert len(test.client.shown_documents) == 1

        params = test.client.shown_documents.pop()
        assert params.uri == f"http://localhost:{port}"
        assert params.external, "Expected 'external' flag to be set"

    finally:
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_preview_no_show():
    """Ensure that the preview command returns a port number and does not make a
    ``window/showDocument`` request when asked."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)
    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(log_level="debug")
                ),
            )
        )

        result = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(
                command=ESBONIO_SERVER_PREVIEW, arguments=[{"show": False}]
            )
        )

        assert "port" in result
        assert result["port"] > 0

        assert len(test.client.messages) == 0
        assert len(test.client.shown_documents) == 0

    finally:
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_preview_multiple_calls():
    """Ensure that multiple calls to the preview command returns the same port number
    i.e. an existing server process is reused."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)
    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    server=SphinxServerConfig(log_level="debug")
                ),
            )
        )

        result = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(
                command=ESBONIO_SERVER_PREVIEW, arguments=[{"show": False}]
            )
        )

        assert "port" in result
        port = result["port"]
        assert port > 0

        assert len(test.client.messages) == 0
        assert len(test.client.shown_documents) == 0

        result = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(
                command=ESBONIO_SERVER_PREVIEW, arguments=[{"show": False}]
            )
        )

        assert "port" in result
        assert port == result["port"]

        assert len(test.client.messages) == 0
        assert len(test.client.shown_documents) == 0

    finally:
        await test.client.shutdown_session()
        await test.stop()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@pytest.mark.parametrize("builder", ["epub", "man", "latex"])
async def test_preview_wrong_builder(builder):
    """Ensure that the preview is only started for supported builders."""

    root_path = pathlib.Path(__file__).parent / "workspace"
    root_uri = uri.from_fs_path(str(root_path))

    config = ClientServerConfig(
        client_factory=make_esbonio_client,
        server_command=[sys.executable, "-m", "esbonio"],
    )

    test = make_client_server(config)
    try:
        test.start()
        await test.client.initialize_session(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=root_uri,
                initialization_options=InitializationOptions(
                    sphinx=SphinxConfig(builder_name=builder)
                ),
            )
        )

        result = await test.client.workspace_execute_command_async(
            ExecuteCommandParams(command=ESBONIO_SERVER_PREVIEW)
        )

        assert result == {}
        assert len(test.client.messages) == 1

        message = test.client.messages[0]
        assert (
            message.message
            == f"Previews are not currently supported for the '{builder}' builder."
        )

    finally:
        await test.client.shutdown_session()
        await test.stop()


def resolve_path(value: str, root_path: pathlib.Path) -> str:
    if value.startswith("$"):
        return value

    return str(pathlib.Path(value.replace("ROOT", str(root_path))).resolve())


def to_snake_case(name: str) -> str:
    """Convert camel case to snake case."""
    s = ""

    for c in name:
        if c.isupper():
            s += f"_{c.lower()}"
            continue

        s += c

    return s
