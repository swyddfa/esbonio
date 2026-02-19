from __future__ import annotations

import logging
import os
import pathlib
import sys
import typing

import pytest
from lsprotocol import types
from pygls import IS_WIN
from pygls.workspace import Workspace

from esbonio.server import EsbonioLanguageServer
from esbonio.server import Uri
from esbonio.server.features.sphinx_manager import SphinxConfig
from esbonio.server.features.sphinx_manager import SubProcess
from esbonio.server.features.sphinx_manager.config import get_module_path
from esbonio.server.features.sphinx_manager.config import register_structure_hooks

if typing.TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


# Default values
PYTHON_CMD = ["/bin/python"]
BUILD_CMD = ["sphinx-build", "-M", "html", "src", "dest"]
PYPATH = [pathlib.Path("/path/to/site-packages/esbonio")]
ENV = {
    "PYTHONUNBUFFERED": "1",
    "PYTHONPATH": str(get_module_path("esbonio.sphinx_agent")),
}
CWD = r"c:\path\to\workspace" if IS_WIN else "/path/to/workspace"


# The value of FALLBACK_ENV must actually exist somewhere on the filesystem
# But for the tests here, the actual location doesn't really matter
FALLBACK_ENV = str(pathlib.Path(__file__).parent)


def mk_uri(path: str) -> str:
    return str(Uri.for_file(path))


@pytest.mark.parametrize(
    "uri, workspace, config, expected",
    [
        (  # If everything is specified, resolve should be a no-op
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD, cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD, cwd=CWD, env=ENV),
                build_command=BUILD_CMD,
            ),
        ),
        (  # If no cwd is given, and there is no available workspace root the config
            # should be considered invalid
            "file:///path/to/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD),
                build_command=BUILD_CMD,
            ),
            None,
        ),
        (  # If the workspace is empty, we should still be able to progress as long as
            # the user provides a cwd
            "file:///path/to/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD, cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD, cwd=CWD, env=ENV),
                build_command=BUILD_CMD,
            ),
        ),
        pytest.param(  # If only a ``root_uri`` is given use that.
            "file:///path/to/workspace/file.rst",
            Workspace(mk_uri(CWD)),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD, cwd=CWD, env=ENV),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # If only a ``root_uri`` is given use that.
            "file:///c:/path/to/workspace/file.rst",
            Workspace(mk_uri(CWD)),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD, cwd=CWD, env=ENV),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        (  # Assuming that the requested uri resides within it.
            "file:///path/to/other/workspace/file.rst",
            Workspace(mk_uri(CWD)),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD),
                build_command=BUILD_CMD,
            ),
            None,
        ),
        pytest.param(  # Otherwise, prefer workspace_folders.
            "file:///path/to/workspace/file.rst",
            Workspace(
                "file:///path/to",
                workspace_folders=[types.WorkspaceFolder(mk_uri(CWD), "workspace")],
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD, cwd=CWD, env=ENV),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(  # Otherwise, prefer workspace_folders.
            "file:///c:/path/to/workspace/file.rst",
            Workspace(
                "file:///c:/path/to",
                workspace_folders=[types.WorkspaceFolder(mk_uri(CWD), "workspace")],
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD, cwd=CWD, env=ENV),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        (  # Handle multi-root scenarios.
            "file:///path/to/workspace-b/file.rst",
            Workspace(
                "file:///path/to",
                workspace_folders=[
                    types.WorkspaceFolder("file:///path/to/workspace-a", "workspace-a"),
                    types.WorkspaceFolder("file:///path/to/workspace-b", "workspace-b"),
                ],
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=PYTHON_CMD,
                    cwd=os.path.join(".", "path", "to", "workspace-b")[1:],
                    env=ENV,
                ),
                build_command=BUILD_CMD,
            ),
        ),
        (  # Again, make sure the requested uri resides within the workspace.
            "file:///path/for/workspace-c/file.rst",
            Workspace(
                "file:///path/to",
                workspace_folders=[
                    types.WorkspaceFolder("file:///path/to/workspace-a", "workspace-a"),
                    types.WorkspaceFolder("file:///path/to/workspace-b", "workspace-b"),
                ],
            ),
            SphinxConfig(
                python_command=SubProcess(command=PYTHON_CMD),
                build_command=BUILD_CMD,
            ),
            None,
        ),
        (  # If no python command provided, fallback to the server's environment
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=[], cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(command=[sys.executable], cwd=CWD, env=ENV),
                build_command=BUILD_CMD,
            ),
        ),
        (  # Allow the user to specify extra envrionment variables
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(
                    command=PYTHON_CMD, cwd=CWD, env={"MY_VAR": "some-value"}
                ),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=PYTHON_CMD,
                    cwd=CWD,
                    env={
                        **ENV,
                        "MY_VAR": "some-value",
                    },
                ),
                build_command=BUILD_CMD,
            ),
        ),
        (  # Or override existing variables in the envrionment
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(
                    command=PYTHON_CMD, cwd=CWD, env={"HOME": "/home/not-really-a-user"}
                ),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=PYTHON_CMD,
                    cwd=CWD,
                    env={
                        **ENV,
                        "HOME": "/home/not-really-a-user",
                    },
                ),
                build_command=BUILD_CMD,
            ),
        ),
        (  # But if the user sets their own PYTHONPATH, be sure to include it alongside our own
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(
                    command=PYTHON_CMD, cwd=CWD, env={"PYTHONPATH": "/extra/py/path"}
                ),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=PYTHON_CMD,
                    cwd=CWD,
                    env={
                        **ENV,
                        "PYTHONPATH": f"{ENV['PYTHONPATH']}{os.pathsep}/extra/py/path",
                    },
                ),
                build_command=BUILD_CMD,
            ),
        ),
        pytest.param(
            # When not on Windows `${venv:/path/to/env}` should expand to
            # `/path/to/env/bin/python`
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=["${venv:/path/to/env}"], cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=["/path/to/env/bin/python"], cwd=CWD, env=ENV
                ),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(
            # When on Windows `${venv:c:/path/to/env}` should expand to
            # `c:/path/to/env/Scripts/python.exe`
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=["${venv:c:/path/to/env}"], cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=["c:\\path\\to\\env\\Scripts\\python.exe"], cwd=CWD, env=ENV
                ),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(
            # When on Windows `${venv:c:\\path\\to\\env}` should expand to
            # `c:/path/to/env/Scripts/python.exe`
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(
                    command=["${venv:c:\\path\\to\\env}"], cwd=CWD
                ),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=["c:\\path\\to\\env\\Scripts\\python.exe"], cwd=CWD, env=ENV
                ),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(
            # When not on Windows `${venv:env}` should expand to
            # `${cwd}/env/bin/python`
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=["${venv:env}"], cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=["/path/to/workspace/env/bin/python"], cwd=CWD, env=ENV
                ),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(
            # When on Windows `${venv:env}` should expand to
            # `c:/path/to/workspace/env/Scripts/python.exe`
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=["${venv:env}"], cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=["c:\\path\\to\\workspace\\env\\Scripts\\python.exe"],
                    cwd=CWD,
                    env=ENV,
                ),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(
            # When not on Windows `${venv:../env}` should expand to
            # `${cwd}/../env/bin/python`
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=["${venv:../env}"], cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=["/path/to/env/bin/python"], cwd=CWD, env=ENV
                ),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(IS_WIN, reason="windows"),
        ),
        pytest.param(
            # When on Windows `${venv:../env}` should expand to
            # `c:/path/to/workspace/Scripts/python.exe`
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=["${venv:../env}"], cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=["c:\\path\\to\\env\\Scripts\\python.exe"], cwd=CWD, env=ENV
                ),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
        pytest.param(
            # When on Windows `${venv:..\\env}` should expand to
            # `c:/path/to/workspace/Scripts/python.exe`
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=SubProcess(command=["${venv:..\\env}"], cwd=CWD),
                build_command=BUILD_CMD,
            ),
            SphinxConfig(
                python_command=SubProcess(
                    command=["c:\\path\\to\\env\\Scripts\\python.exe"], cwd=CWD, env=ENV
                ),
                build_command=BUILD_CMD,
            ),
            marks=pytest.mark.skipif(not IS_WIN, reason="windows only"),
        ),
    ],
)
def test_resolve(
    uri: str,
    workspace: Workspace,
    config: SphinxConfig,
    expected: SphinxConfig | None,
):
    """Ensure that we can resolve a user's configuration correctly.

    Parameters
    ----------
    uri
       The uri the config should be resolved relative to

    workspace
       The workspace in which to resolve the configuration

    config
       The base configuration to resolve

    expected
       The expected outcome
    """
    actual = config.resolve(Uri.parse(uri), workspace, logger)

    if expected is None:
        assert actual is None
        return

    assert actual is not None
    assert actual.enable_dev_tools == expected.enable_dev_tools
    assert actual.build_command == expected.build_command
    assert actual.config_overrides == expected.config_overrides

    assert actual.python_command.command == expected.python_command.command
    assert actual.python_command.cwd == expected.python_command.cwd

    # Since we pass through the current environment, check each expected key individually
    for varname in expected.python_command.env:
        assert (
            actual.python_command.env[varname] == expected.python_command.env[varname]
        )


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, SphinxConfig()),
        (
            {"pythonCommand": ["/bin/python"]},
            SphinxConfig(python_command=SubProcess(["/bin/python"])),
        ),
        (
            {"pythonCommand": {"command": ["/bin/python"]}},
            SphinxConfig(python_command=SubProcess(["/bin/python"])),
        ),
        (
            {"buildCommand": ["-M", "html", "src", "dest"]},
            SphinxConfig(build_command=["-M", "html", "src", "dest"]),
        ),
        (
            {"buildArguments": ["-M", "html", "src", "dest"]},
            SphinxConfig(build_command=["-M", "html", "src", "dest"]),
        ),
    ],
)
def test_structure_config(value: dict[str, Any], expected: SphinxConfig):
    """Ensure that we can structure a SphinxConfig instance from raw configuration
    values correctly."""

    server = EsbonioLanguageServer()
    register_structure_hooks(server.converter)

    actual = server.converter.structure(value, SphinxConfig)
    assert expected == actual
