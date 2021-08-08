import asyncio
import pathlib
import tempfile
from typing import Any
from typing import Dict

import py.test
import pygls.uris as uri
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CLOSE
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.methods import TEXT_DOCUMENT_DID_SAVE
from pygls.lsp.methods import WORKSPACE_EXECUTE_COMMAND
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DiagnosticSeverity
from pygls.lsp.types import DidChangeTextDocumentParams
from pygls.lsp.types import DidCloseTextDocumentParams
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import ExecuteCommandParams
from pygls.lsp.types import MessageType
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import TextDocumentContentChangeTextEvent
from pygls.lsp.types import TextDocumentIdentifier
from pygls.lsp.types import TextDocumentItem
from pygls.lsp.types import VersionedTextDocumentIdentifier

from esbonio.lsp import BUILTIN_MODULES
from esbonio.lsp import create_language_server
from esbonio.lsp import SphinxLanguageServer
from esbonio.lsp.sphinx import InitializationOptions
from esbonio.lsp.sphinx import SphinxConfig
from esbonio.lsp.testing import ClientServer


@py.test.fixture(scope="function")
async def cs():
    """A disposable version of the 'client_server' fixture.

    - It's disposable in that only lives for a single test.
    - Unlike 'client_server' it has to be started by the test case, this letting us test
      startup logic
    """

    server = create_language_server(
        SphinxLanguageServer, BUILTIN_MODULES, loop=asyncio.new_event_loop()
    )

    test = ClientServer(server)
    yield test
    # Test cleanup.
    await test.stop()


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "root,options,expected",
    [
        (  # Ensure the defaults work
            "sphinx-default",
            SphinxConfig(),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT",
                buildDir=".cache/esbonio",
                builderName="html",
            ),
        ),
        (  # Ensure that we can set confDir to be an explicit path.
            ".",
            SphinxConfig(confDir="ROOT/sphinx-extensions"),
            SphinxConfig(
                confDir="ROOT/sphinx-extensions",
                srcDir="ROOT/sphinx-extensions",
                buildDir=".cache/esbonio",
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir relative to ${workspaceRoot}
            ".",
            SphinxConfig(confDir="${workspaceRoot}/sphinx-extensions"),
            SphinxConfig(
                confDir="ROOT/sphinx-extensions",
                srcDir="ROOT/sphinx-extensions",
                buildDir=".cache/esbonio",
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy confDir to be exactly ${workspaceRoot}
            "sphinx-extensions",
            SphinxConfig(confDir="${workspaceRoot}"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT",
                buildDir=".cache/esbonio",
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy srcDir to be an exact path
            "sphinx-srcdir",
            SphinxConfig(srcDir="ROOT/../sphinx-default"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT/../sphinx-default",
                buildDir=".cache/esbonio",
                builderName="html",
            ),
        ),
        (  # Ensure that we can specify srcDir relative to ${workspaceRoot}
            ".",
            SphinxConfig(
                confDir="${workspaceRoot}/sphinx-srcdir",
                srcDir="${workspaceRoot}/sphinx-default",
            ),
            SphinxConfig(
                confDir="ROOT/sphinx-srcdir",
                srcDir="ROOT/sphinx-default",
                buildDir=".cache/esbonio",
                builderName="html",
            ),
        ),
        (  # Ensure that we can specify srcDir to be exactly ${confDir}
            "sphinx-extensions",
            SphinxConfig(srcDir="${confDir}"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT",
                buildDir=".cache/esbonio",
                builderName="html",
            ),
        ),
        (  # Ensure that we can specifiy srcDir to be relative to ${confDir}
            "sphinx-srcdir",
            SphinxConfig(srcDir="${confDir}/../sphinx-default"),
            SphinxConfig(
                confDir="ROOT",
                srcDir="ROOT/../sphinx-default",
                buildDir=".cache/esbonio",
                builderName="html",
            ),
        ),
    ],
)
async def test_initialization(cs, testdata, root, options, expected):
    """Ensure that the server responds correctly to various initialization options."""

    root_path = str(testdata(root, path_only=True))
    root_uri = uri.from_fs_path(root_path)

    for key, value in options.dict().items():
        if key not in {"builder_name"} and value is not None:
            path = resolve_path(value, root_path)
            setattr(options, key, str(path))

    init_options = InitializationOptions(sphinx=options)

    test = cs  # type: ClientServer
    await test.start(root_uri, initialization_options=init_options)

    configuration = await test.client.lsp.send_request_async(
        WORKSPACE_EXECUTE_COMMAND,
        ExecuteCommandParams(command="esbonio.server.configuration"),
    )

    assert len(test.client.messages) == 0

    assert "sphinx" in configuration
    actual = SphinxConfig(**configuration["sphinx"])

    assert actual.version is not None
    assert actual.conf_dir == resolve_path(expected.conf_dir, root_path)
    assert actual.src_dir == resolve_path(expected.src_dir, root_path)
    assert expected.build_dir in actual.build_dir
    assert actual.builder_name == expected.builder_name


@py.test.mark.asyncio
async def test_initialization_build_dir(cs, testdata):
    """Ensure that we can set the build_dir."""

    root_path = str(testdata("sphinx-default", path_only=True))
    root_uri = uri.from_fs_path(root_path)

    with tempfile.TemporaryDirectory() as build_dir:
        init_options = InitializationOptions(sphinx=SphinxConfig(buildDir=build_dir))

        test = cs  # type: ClientServer
        await test.start(root_uri, initialization_options=init_options)

        configuration = await test.client.lsp.send_request_async(
            WORKSPACE_EXECUTE_COMMAND,
            ExecuteCommandParams(command="esbonio.server.configuration"),
        )

        assert len(test.client.messages) == 0

        assert "sphinx" in configuration
        actual = SphinxConfig(**configuration["sphinx"])

        assert actual.version is not None
        assert actual.conf_dir == root_path
        assert actual.src_dir == root_path
        assert actual.build_dir == str(pathlib.Path(build_dir, "html"))
        assert actual.builder_name == "html"


@py.test.mark.asyncio
async def test_initialization_sphinx_error(cs, testdata):
    """Ensure that the user is notified when we Sphinx throws an exception."""

    root_path = str(testdata("sphinx-error", path_only=True))
    root_uri = uri.from_fs_path(root_path)

    test = cs  # type: ClientServer
    await test.start(root_uri, wait=False)

    configuration = await test.client.lsp.send_request_async(
        WORKSPACE_EXECUTE_COMMAND,
        ExecuteCommandParams(command="esbonio.server.configuration"),
    )

    assert "sphinx" in configuration
    assert configuration["sphinx"]["version"] is None

    assert len(test.client.messages) == 1
    message = test.client.messages[0]

    assert message.type == MessageType.Error.value
    assert message.message.startswith("Unable to initialize Sphinx")


@py.test.mark.asyncio
async def test_initialization_build_error(cs, testdata):
    """Ensure that the user is notified when we can't build the docs."""

    root_path = testdata("sphinx-srcdir", path_only=True)  # type: pathlib.Path
    index_rst = root_path / "index.rst"
    root_uri = uri.from_fs_path(str(root_path))

    # Depending on the order in which the tests run, there may be an index.rst
    # file hanging around that we have to delete.
    if index_rst.exists():
        index_rst.unlink()

    test = cs  # type: ClientServer
    await test.start(root_uri)

    configuration = await test.client.lsp.send_request_async(
        WORKSPACE_EXECUTE_COMMAND,
        ExecuteCommandParams(command="esbonio.server.configuration"),
    )

    assert "sphinx" in configuration
    assert configuration["sphinx"]["version"] is not None

    assert len(test.client.messages) == 1
    message = test.client.messages[0]

    assert message.type == MessageType.Error.value
    assert message.message.startswith("Unable to build documentation")


@py.test.mark.asyncio
async def test_initialization_missing_conf(cs, testdata):
    """Ensure that the user is notified when we can't find their 'conf.py'."""

    with tempfile.TemporaryDirectory() as root_dir:
        root_uri = uri.from_fs_path(root_dir)

        test = cs  # type: ClientServer
        await test.start(root_uri, wait=False)

        configuration = await test.client.lsp.send_request_async(
            WORKSPACE_EXECUTE_COMMAND,
            ExecuteCommandParams(command="esbonio.server.configuration"),
        )

        assert "sphinx" in configuration
        assert configuration["sphinx"]["version"] is None

        assert len(test.client.messages) == 1
        message = test.client.messages[0]

        assert message.type == MessageType.Warning.value
        assert message.message.startswith("Unable to find your 'conf.py'")


@py.test.mark.asyncio
@py.test.mark.parametrize(
    "good,bad,expected",
    [
        py.test.param(
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
            marks=py.test.mark.skip(
                reason="Sphinx seems to have stopped reporting this one?"
            ),
        ),
        (
            ".. image:: ../sphinx-default/_static/vscode-screenshot.png",
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
async def test_diagnostics(event_loop, testdata, client_server, good, bad, expected):
    """Ensure that we can correctly convert Sphinx errors/warnings into diagnostics.

    This test is quite involved as we have to ensure both the language server and the
    filesystem are in agreement on the contents of the ``sphinx-srcdir/`` directory so
    that both Sphinx and the language server can do their thing.
    """

    # Setup, start with the file in the "good" state.
    workspace_root = testdata("sphinx-srcdir", path_only=True)
    test_path = workspace_root / "index.rst"

    with test_path.open("w") as f:
        f.write(good)

    test = await client_server("sphinx-srcdir")  # type: ClientServer
    assert test.server.workspace.root_uri == uri.from_fs_path(str(workspace_root))
    test_uri = uri.from_fs_path(str(test_path))

    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_OPEN,
        DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=test_uri, language_id="rst", version=1, text=good
            )
        ),
    )

    # Change the file so that it's in the "bad" state, we should see a diagnostic
    # reporting the issue.
    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_CHANGE,
        DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=test_uri, version=2),
            content_changes=[TextDocumentContentChangeTextEvent(text=bad)],
        ),
    )

    with test_path.open("w") as f:
        f.write(bad)

    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_SAVE,
        DidSaveTextDocumentParams(
            text_document=TextDocumentIdentifier(uri=test_uri), text=bad
        ),
    )

    await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
    actual = test.client.diagnostics[test_uri][0]

    assert Range(**object_to_dict(actual.range)) == expected.range
    assert actual.severity == expected.severity
    assert actual.message == expected.message
    assert actual.source == expected.source

    with test_path.open("w") as f:
        f.write(good)

    # Undo the changes, we should see the diagnostic be removed.
    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_CHANGE,
        DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=test_uri, version=3),
            content_changes=[TextDocumentContentChangeTextEvent(text=good)],
        ),
    )

    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_SAVE,
        DidSaveTextDocumentParams(
            text_document=TextDocumentIdentifier(uri=test_uri), text=good
        ),
    )

    # Ensure that we remove any resolved diagnostics.

    await test.client.lsp.wait_for_notification_async("esbonio/buildComplete")
    assert len(test.client.diagnostics[test_uri]) == 0

    # Cleanup
    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_CLOSE,
        DidCloseTextDocumentParams(text_document=TextDocumentIdentifier(uri=test_uri)),
    )
    test_path.unlink()


def resolve_path(value: str, root_path: str) -> str:

    if value.startswith("$"):
        return value

    return str(pathlib.Path(value.replace("ROOT", root_path)).resolve())


def object_to_dict(obj) -> Dict[str, Any]:
    """Convert a pygls.protocol.Object to a dictionary."""

    if hasattr(obj, "_asdict"):
        return {k: object_to_dict(v) for k, v in obj._asdict().items()}

    return obj
