import itertools
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar

import attrs
import pytest
from lsprotocol import types
from pygls import IS_WIN
from pygls.workspace import Workspace

from esbonio.server import EsbonioLanguageServer
from esbonio.server import Uri
from esbonio.server._configuration import _merge_configs
from esbonio.server._configuration import _uri_to_scope

T = TypeVar("T")


@attrs.define
class ExampleConfig:
    log_level: str = "error"
    log_names: List[str] = attrs.field(factory=list)


@attrs.define
class ColorConfig:
    color: str
    scope: str = attrs.field(default="${scope}")


@pytest.fixture
def server(event_loop):
    """Return a server instance for testing."""
    _server = EsbonioLanguageServer(loop=event_loop)
    return _server


@pytest.mark.parametrize(
    "init_options,workspace_config,file_config,section,spec,scope,expected",
    [
        pytest.param(  # When there's no configuration at all, just return the defaults.
            {},
            {},
            {},
            "esbonio.server",
            ExampleConfig,
            None,
            ExampleConfig(log_level="error", log_names=[]),
            id="no-config",
        ),
        pytest.param(
            dict(esbonio=dict(server=dict(logLevel="info"))),
            {},
            {},
            "esbonio.server",
            ExampleConfig,
            None,
            ExampleConfig(log_level="info", log_names=[]),
            id="init-options",
        ),
        pytest.param(  # Handle the case where the client omits the top-level namespace
            dict(server=dict(logLevel="info")),
            {},
            {},
            "esbonio.server",
            ExampleConfig,
            None,
            ExampleConfig(log_level="info", log_names=[]),
            id="init-options-no-namespace",
        ),
        pytest.param(
            {},
            {"": dict(esbonio=dict(server=dict(logLevel="info")))},
            {},
            "esbonio.server",
            ExampleConfig,
            None,
            ExampleConfig(log_level="info", log_names=[]),
            id="global-workspace-config",
        ),
        pytest.param(
            {},
            {
                "file:///path/to/workspace": dict(
                    esbonio=dict(server=dict(logLevel="info"))
                )
            },
            {},
            "esbonio.server",
            ExampleConfig,
            "file:///path/to/workspace/file.txt",
            ExampleConfig(log_level="info", log_names=[]),
            id="workspace-config[unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(
            {},
            {
                "file:///c%3A/path/to/workspace": dict(
                    esbonio=dict(server=dict(logLevel="info"))
                )
            },
            {},
            "esbonio.server",
            ExampleConfig,
            "file:///c:/path/to/workspace/file.txt",
            ExampleConfig(log_level="info", log_names=[]),
            id="workspace-config[win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(  # Handle the case where the scope does not match a known workspace
            {},
            {
                "file:///path/to/workspace": dict(
                    esbonio=dict(server=dict(logLevel="info"))
                )
            },
            {},
            "esbonio.server",
            ExampleConfig,
            "file:///path/to/other/workspace/file.txt",
            ExampleConfig(log_level="error", log_names=[]),
            id="workspace-config-scope-mismatch[unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # Handle the case where the scope does not match a known workspace
            {},
            {
                "file:///c%3A/path/to/workspace": dict(
                    esbonio=dict(server=dict(logLevel="info"))
                )
            },
            {},
            "esbonio.server",
            ExampleConfig,
            "file:///c:/path/to/other/workspace/file.txt",
            ExampleConfig(log_level="error", log_names=[]),
            id="workspace-config-scope-mismatch[win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(  # Handle the case where the scope does not match a known file
            {},
            {},
            {
                "file:///path/to/workspace/docs": dict(
                    esbonio=dict(server=dict(logLevel="info"))
                )
            },
            "esbonio.server",
            ExampleConfig,
            "file:///path/to/workspace/docs/file.txt",
            ExampleConfig(log_level="info", log_names=[]),
            id="file-config[unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # Handle the case where the scope does not match a known file
            {},
            {},
            {
                "file:///c%3A/path/to/workspace/docs": dict(
                    esbonio=dict(server=dict(logLevel="info"))
                )
            },
            "esbonio.server",
            ExampleConfig,
            "file:///c:/path/to/workspace/docs/file.txt",
            ExampleConfig(log_level="info", log_names=[]),
            id="file-config[win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(  # Handle the case where the scope does not match a known file
            {},
            {},
            {
                "file:///path/to/workspace/docs": dict(
                    esbonio=dict(server=dict(logLevel="info"))
                )
            },
            "esbonio.server",
            ExampleConfig,
            "file:///path/to/workspace/workspace/file.txt",
            ExampleConfig(log_level="error", log_names=[]),
            id="file-config-scope-mismatch[unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # Handle the case where the scope does not match a known file
            {},
            {},
            {
                "file:///c%3A/path/to/workspace/docs": dict(
                    esbonio=dict(server=dict(logLevel="info"))
                )
            },
            "esbonio.server",
            ExampleConfig,
            "file:///c:/path/to/workspace/workspace/file.txt",
            ExampleConfig(log_level="error", log_names=[]),
            id="file-config-scope-mismatch[win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(  # Allow the client to override the file based config
            {},
            {
                "file:///path/to/workspace": dict(
                    esbonio=dict(server=dict(logLevel="debug"))
                )
            },
            {
                "file:///path/to/workspace/docs": dict(
                    esbonio=dict(server=dict(logLevel="info", logNames=["file"]))
                )
            },
            "esbonio.server",
            ExampleConfig,
            "file:///path/to/workspace/docs/file.txt",
            ExampleConfig(log_level="debug", log_names=["file"]),
            id="workspace-file-override[unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # Allow the client to override the file based config
            {},
            {
                "file:///c%3A/path/to/workspace": dict(
                    esbonio=dict(server=dict(logLevel="debug"))
                )
            },
            {
                "file:///c%3A/path/to/workspace/docs": dict(
                    esbonio=dict(server=dict(logLevel="info", logNames=["file"]))
                )
            },
            "esbonio.server",
            ExampleConfig,
            "file:///c:/path/to/workspace/docs/file.txt",
            ExampleConfig(log_level="debug", log_names=["file"]),
            id="workspace-file-override[win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(  # Check that we can expand config variables correctly
            {},
            {
                "file:///path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {},
            "esbonio.colors",
            ColorConfig,
            "file:///path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="file:///path/to/workspace"),
            id="scope-variable[workspace][unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # Check that we can expand config variables correctly
            {},
            {
                "file:///c%3A/path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {},
            "esbonio.colors",
            ColorConfig,
            "file:///c:/path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="file:///c%3A/path/to/workspace"),
            id="scope-variable[workspace][win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(  # Check that we can expand config variables correctly
            {},
            {
                "file:///path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {
                "file:///path/to/workspace/docs": dict(
                    esbonio=dict(colors=dict(color="blue"))
                ),
            },
            "esbonio.colors",
            ColorConfig,
            "file:///path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="file:///path/to/workspace/docs"),
            id="scope-variable[workspace+file][unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # Check that we can expand config variables correctly
            {},
            {
                "file:///c%3A/path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {
                "file:///c%3A/path/to/workspace/docs": dict(
                    esbonio=dict(colors=dict(color="blue"))
                ),
            },
            "esbonio.colors",
            ColorConfig,
            "file:///c:/path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="file:///c%3A/path/to/workspace/docs"),
            id="scope-variable[workspace+file][win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(  # The user should still be able to override them
            {},
            {
                "file:///path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {
                "file:///path/to/workspace/docs": dict(
                    esbonio=dict(colors=dict(color="blue", scope="file:///my/scope"))
                ),
            },
            "esbonio.colors",
            ColorConfig,
            "file:///path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="file:///my/scope"),
            id="scope-variable-override[unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # The user should still be able to override them
            {},
            {
                "file:///c%3A/path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {
                "file:///c%3A/path/to/workspace/docs": dict(
                    esbonio=dict(colors=dict(color="blue", scope="file:///my/scope"))
                ),
            },
            "esbonio.colors",
            ColorConfig,
            "file:///c:/path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="file:///my/scope"),
            id="scope-variable-override[win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(
            {},
            {
                "file:///path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {
                "file:///path/to/workspace/docs": dict(
                    esbonio=dict(colors=dict(color="blue", scope="${scopePath}"))
                ),
            },
            "esbonio.colors",
            ColorConfig,
            "file:///path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="/path/to/workspace/docs"),
            id="scope-path-variable[unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(
            {},
            {
                "file:///c%3A/path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {
                "file:///c%3A/path/to/workspace/docs": dict(
                    esbonio=dict(colors=dict(color="blue", scope="${scopePath}"))
                ),
            },
            "esbonio.colors",
            ColorConfig,
            "file:///c:/path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="/c:/path/to/workspace/docs"),
            id="scope-path-variable[win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(
            {},
            {
                "file:///path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {
                "file:///path/to/workspace/docs": dict(
                    esbonio=dict(colors=dict(color="blue", scope="${scopeFsPath}"))
                ),
            },
            "esbonio.colors",
            ColorConfig,
            "file:///path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="/path/to/workspace/docs"),
            id="scope-fspath-variable[unix]",
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(
            {},
            {
                "file:///c%3A/path/to/workspace": dict(
                    esbonio=dict(colors=dict(color="red"))
                ),
            },
            {
                "file:///c%3A/path/to/workspace/docs": dict(
                    esbonio=dict(colors=dict(color="blue", scope="${scopeFsPath}"))
                ),
            },
            "esbonio.colors",
            ColorConfig,
            "file:///c:/path/to/workspace/docs/file.txt",
            ColorConfig(color="red", scope="c:\\path\\to\\workspace\\docs"),
            id="scope-fspath-variable[win]",
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
    ],
)
def test_get_configuration(
    server: EsbonioLanguageServer,
    init_options: Dict[str, Any],
    workspace_config: Dict[str, Any],
    file_config: Dict[str, Any],
    section: str,
    spec: Type[T],
    scope: Optional[str],
    expected: T,
):
    """Ensure that we can get configuration values correctly.

    The number of parameters to this test case is a lot! But the test itself is fairly
    simple. Given the current configuration of the server, can we resolve the
    configuration correctly and return the expected set of values?

    Parameters
    ----------
    init_options
       The server's initialization options.

    workspace_config
       The server's cached ``workspace/configuration`` requests

    file_config
       The server's cached config coming from configuration files

    section
       The configuration section to retrieve

    spec
       The datatype describing the configuration

    scope
       The scope at which to get the configuration

    expected
       The expected value.
    """
    server.configuration.initialization_options = init_options
    server.configuration._workspace_config = workspace_config
    server.configuration._file_config = file_config

    # Infer the workspace based on the given config.
    workspace_folders = [
        types.WorkspaceFolder(uri=uri, name=f"workspace-{idx}")
        for idx, uri in enumerate(workspace_config.keys())
        if uri != ""
    ]
    server.lsp._workspace = Workspace(None, workspace_folders=workspace_folders)

    scope_uri = Uri.parse(scope) if scope else None

    actual = server.configuration.get(section, spec, scope=scope_uri)
    assert actual == expected


@pytest.mark.parametrize(
    "known_scopes,setup",
    [
        *itertools.product(
            [
                ["file:///path/to/test"],
            ],
            [
                ("file:///path/to/test/file.txt", "file:///path/to/test"),
                ("file:///path/to/other/file.txt", ""),
                (None, ""),
            ],
        ),
        *itertools.product(
            [
                ["file:///path/to/test", "file:///path/to/test/sub/folder"],
            ],
            [
                ("file:///path/to/test/file.txt", "file:///path/to/test"),
                ("file:///path/to/test/sub/file.txt", "file:///path/to/test"),
                (
                    "file:///path/to/test/sub/folder/file.txt",
                    "file:///path/to/test/sub/folder",
                ),
            ],
        ),
    ],
)
@pytest.mark.skipif(IS_WIN, reason="windows")
def test_uri_to_scope(known_scopes, setup):
    """Ensure that we can determine the correct scope for the given uri."""

    uri, expected = setup
    parsed_uri = Uri.parse(uri) if uri else None
    scope = _uri_to_scope(known_scopes, parsed_uri)
    assert scope == expected


@pytest.mark.parametrize(
    "known_scopes,setup",
    [
        *itertools.product(
            [
                ["file:///c:/path/to/test", "file:///c:/path/to/test/sub/folder"],
            ],
            [
                ("file:///c:/path/to/test/file.txt", "file:///c%3A/path/to/test"),
                ("file:///c%3A/path/to/test/file.txt", "file:///c%3A/path/to/test"),
                ("file:///C:/path/to/test/file.txt", "file:///c%3A/path/to/test"),
                ("file:///C%3A/path/to/test/file.txt", "file:///c%3A/path/to/test"),
                ("file:///c:/path/to/test/sub/file.txt", "file:///c%3A/path/to/test"),
                (
                    "file:///c:/path/to/test/sub/folder/file.txt",
                    "file:///c%3A/path/to/test/sub/folder",
                ),
            ],
        ),
    ],
)
@pytest.mark.skipif(not IS_WIN, reason="windows only")
def test_uri_to_scope_windows(known_scopes, setup):
    """Ensure that we can determine the correct scope for the given uri."""

    uri, expected = setup
    scope = _uri_to_scope(known_scopes, Uri.parse(uri))
    assert scope == expected


@pytest.mark.parametrize(
    "configs, expected",
    [
        (  # Last value wins
            [
                {"a": 1},
                {"a": 3},
                {"a": 2},
            ],
            {"a": 2},
        ),
        (  # None is a valid value
            [
                {"a": 1},
                {"a": 2},
                {"a": None},
            ],
            {"a": None},
        ),
        (  # Simple merge
            [
                {"a": 1},
                {"b": 3},
                {"c": 2},
            ],
            {"a": 1, "b": 3, "c": 2},
        ),
        (  # Ensure nested values are merged as well
            [
                {"a": 1, "b": {"c": 1}},
                {"b": {"c": 4}},
                {"b": {"d": 7}},
            ],
            {"a": 1, "b": {"c": 4, "d": 7}},
        ),
        (  # Handle the case where there's a type mismatch.
            [
                {"a": {"c": 1}},
                {"a": 2},
                {"a": {"d": 7}},
            ],
            {"a": {"c": 1, "d": 7}},
        ),
        (  # Let the final config dictate the type of a given field.
            [
                {"a": {"c": 1}},
                {"a": {"d": 7}},
                {"a": 2},
            ],
            {"a": 2},
        ),
    ],
)
def test_merge_configs(configs, expected):
    """Ensure that we can merge configurations together correctly."""
    assert expected == _merge_configs(*configs)
