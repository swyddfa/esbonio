import pathlib
import sys

import pytest_lsp
from lsprotocol import types
from pytest_lsp import ClientServerConfig
from pytest_lsp import LanguageClient

SERVER_CMD = ["-m", "esbonio"]
TEST_DIR = pathlib.Path(__file__).parent.parent


@pytest_lsp.fixture(
    scope="session",
    config=ClientServerConfig(
        server_command=[sys.executable, *SERVER_CMD],
    ),
)
async def client(lsp_client: LanguageClient, uri_for, tmp_path_factory):
    """The "main" client to use for our tests."""
    build_dir = tmp_path_factory.mktemp("build")
    workspace_uri = uri_for("workspaces", "demo")
    test_uri = workspace_uri / "index.rst"

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
                "logging": {"level": "debug"},
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
                types.WorkspaceFolder(uri=str(workspace_uri), name="demo"),
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
