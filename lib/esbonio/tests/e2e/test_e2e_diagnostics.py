import pathlib
import sys

import pytest
import pytest_lsp
from lsprotocol import types
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient

SERVER_CMD = ["-m", "esbonio"]
TEST_DIR = pathlib.Path(__file__).parent.parent


@pytest_lsp.fixture(
    scope="module",
    config=ClientServerConfig(
        server_command=[sys.executable, *SERVER_CMD],
    ),
)
async def pull_client(lsp_client: LanguageClient, uri_for, tmp_path_factory):
    """A client that supports the pull-diagnostics model."""
    build_dir = tmp_path_factory.mktemp("build")
    workspace_uri = uri_for("sphinx-default", "workspace")
    test_uri = workspace_uri / "definitions.rst"

    await lsp_client.initialize_session(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(
                # Signal pull diagnostic support
                text_document=types.TextDocumentClientCapabilities(
                    diagnostic=types.DiagnosticClientCapabilities(
                        dynamic_registration=False
                    )
                ),
                # Signal workDoneProgress/create support.
                window=types.WindowClientCapabilities(
                    work_done_progress=True,
                ),
            ),
            initialization_options={
                "server": {"logLevel": "debug"},
                "sphinx": {
                    "buildCommand": [
                        "sphinx-build",
                        "-M",
                        "html",
                        workspace_uri.fs_path,
                        str(build_dir),
                    ],
                    "pythonCommand": [sys.executable],
                },
            },
            workspace_folders=[
                types.WorkspaceFolder(uri=str(workspace_uri), name="sphinx-default"),
            ],
        )
    )

    # Open a text document to trigger sphinx client creation.
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=str(test_uri),
                language_id="restructuredtext",
                version=0,
                text=pathlib.Path(test_uri).read_text(),
            )
        )
    )

    await lsp_client.wait_for_notification("sphinx/appCreated")

    # Save the document to trigger a build
    lsp_client.text_document_did_save(
        types.DidSaveTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )

    build_finished = False
    while not build_finished:
        await lsp_client.wait_for_notification("$/progress")
        report = list(lsp_client.progress_reports.values())[0][-1]
        build_finished = report.kind == "end"

    yield

    # Teardown
    await lsp_client.shutdown_session()


@pytest.mark.asyncio
@pytest.mark.skip
async def test_document_diagnostic(pull_client: LanguageClient, uri_for):
    """Ensure that we can get the diagnostics for a single document correctly."""

    workspace_uri = uri_for("sphinx-default", "workspace")
    test_uri = workspace_uri / "definitions.rst"
    report = await pull_client.text_document_diagnostic_async(
        types.DocumentDiagnosticParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )

    assert report.kind == "full"

    # We will only check the diagnostic message, full details will be handled by other
    # test cases.
    messages = {d.message for d in report.items}
    assert messages == {
        "image file not readable: _static/bad.png",
        "unknown document: '/changelog'",
    }

    assert len(pull_client.diagnostics) == 0, "Server should not publish diagnostics"


@pytest.mark.asyncio
@pytest.mark.skip
async def test_workspace_diagnostic(pull_client: LanguageClient, uri_for):
    """Ensure that we can get diagnostics for the whole workspace correctly."""
    report = await pull_client.workspace_diagnostic_async(
        types.WorkspaceDiagnosticParams(previous_result_ids=[])
    )

    workspace_uri = uri_for("sphinx-default", "workspace")
    expected = {
        str(workspace_uri / "definitions.rst"): {
            "image file not readable: _static/bad.png",
            "unknown document: '/changelog'",
        },
        str(workspace_uri / "directive_options.rst"): {
            "image file not readable: filename.png",
            "document isn't included in any toctree",
        },
    }
    assert len(report.items) == len(expected)
    for item in report.items:
        assert expected[item.uri] == {d.message for d in item.items}

    assert len(pull_client.diagnostics) == 0, "Server should not publish diagnostics"


@pytest_lsp.fixture(
    scope="module",
    config=ClientServerConfig(
        server_command=[sys.executable, *SERVER_CMD],
    ),
)
async def pub_client(lsp_client: LanguageClient, uri_for, tmp_path_factory):
    """A client that does **not** support the pull-diagnostics model."""
    build_dir = tmp_path_factory.mktemp("build")
    workspace_uri = uri_for("sphinx-default", "workspace")
    test_uri = workspace_uri / "definitions.rst"

    await lsp_client.initialize_session(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(
                # Signal workDoneProgress/create support.
                window=types.WindowClientCapabilities(
                    work_done_progress=True,
                ),
            ),
            initialization_options={
                "server": {"logLevel": "debug"},
                "sphinx": {
                    "buildCommand": [
                        "sphinx-build",
                        "-M",
                        "html",
                        workspace_uri.fs_path,
                        str(build_dir),
                    ],
                    "pythonCommand": [sys.executable],
                },
            },
            workspace_folders=[
                types.WorkspaceFolder(uri=str(workspace_uri), name="sphinx-default"),
            ],
        )
    )

    # Open a text document to trigger sphinx client creation.
    lsp_client.text_document_did_open(
        types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri=str(test_uri),
                language_id="restructuredtext",
                version=0,
                text=pathlib.Path(test_uri).read_text(),
            )
        )
    )

    await lsp_client.wait_for_notification("sphinx/appCreated")

    # Save the document to trigger a build
    lsp_client.text_document_did_save(
        types.DidSaveTextDocumentParams(
            text_document=types.TextDocumentIdentifier(uri=str(test_uri))
        )
    )

    build_finished = False
    while not build_finished:
        await lsp_client.wait_for_notification("$/progress")
        report = list(lsp_client.progress_reports.values())[0][-1]
        build_finished = report.kind == "end"

    yield

    # Teardown
    await lsp_client.shutdown_session()


@pytest.mark.asyncio
@pytest.mark.skip
async def test_publish_diagnostics(pub_client: LanguageClient, uri_for):
    """Ensure that the server publishes the diagnostics it finds"""
    workspace_uri = uri_for("sphinx-default", "workspace")
    expected = {
        str(workspace_uri / "definitions.rst"): {
            "image file not readable: _static/bad.png",
            "unknown document: '/changelog'",
        },
        str(workspace_uri / "directive_options.rst"): {
            "image file not readable: filename.png",
            "document isn't included in any toctree",
        },
    }

    # The server might not have published its diagnostics yet
    while len(pub_client.diagnostics) < len(expected):
        await pub_client.wait_for_notification(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)

    for uri, expected_msgs in expected.items():
        items = pub_client.diagnostics[uri]
        actual_msgs = {d.message for d in items}

        assert expected_msgs == actual_msgs
