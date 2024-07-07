import logging
import os
import pathlib
from typing import Optional

import pytest
from lsprotocol.types import WorkspaceFolder
from pygls.workspace import Workspace

from esbonio.server import Uri
from esbonio.server.features.sphinx_manager import SphinxConfig

logger = logging.getLogger(__name__)


# Default values
CWD = os.path.join(".", "path", "to", "workspace")[1:]
PYTHON_CMD = ["/bin/python"]
BUILD_CMD = ["sphinx-build", "-M", "html", "src", "dest"]
PYPATH = [pathlib.Path("/path/to/site-packages/esbonio")]


def mk_uri(path: str) -> str:
    return str(Uri.for_file(path))


@pytest.mark.parametrize(
    "uri, workspace, config, expected",
    [
        (  # If everything is specified, resolve should be a no-op
            "file:///path/to/workspace/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                cwd=CWD,
                python_path=PYPATH,
            ),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                cwd=CWD,
                python_path=PYPATH,
            ),
        ),
        (  # If no cwd is given, and there is no available workspace root the config
            # should be considered invalid
            "file:///path/to/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
            ),
            None,
        ),
        (  # If the workspace is empty, we should still be able to progress as long as
            # the user provides a cwd
            "file:///path/to/file.rst",
            Workspace(None),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
                cwd=CWD,
            ),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
                cwd=CWD,
            ),
        ),
        (  # If only a ``root_uri`` is given use that.
            "file:///path/to/workspace/file.rst",
            Workspace(mk_uri(CWD)),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
            ),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
                cwd=CWD,
            ),
        ),
        (  # Assuming that the requested uri resides within it.
            "file:///path/to/other/workspace/file.rst",
            Workspace(mk_uri(CWD)),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
            ),
            None,
        ),
        (  # Otherwise, prefer workspace_folders.
            "file:///path/to/workspace/file.rst",
            Workspace(
                "file:///path/to",
                workspace_folders=[WorkspaceFolder(mk_uri(CWD), "workspace")],
            ),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
            ),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
                cwd=CWD,
            ),
        ),
        (  # Handle multi-root scenarios.
            "file:///path/to/workspace-b/file.rst",
            Workspace(
                "file:///path/to",
                workspace_folders=[
                    WorkspaceFolder("file:///path/to/workspace-a", "workspace-a"),
                    WorkspaceFolder("file:///path/to/workspace-b", "workspace-b"),
                ],
            ),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
            ),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
                cwd=os.path.join(".", "path", "to", "workspace-b")[1:],
            ),
        ),
        (  # Again, make sure the requested uri resides within the workspace.
            "file:///path/for/workspace-c/file.rst",
            Workspace(
                "file:///path/to",
                workspace_folders=[
                    WorkspaceFolder("file:///path/to/workspace-a", "workspace-a"),
                    WorkspaceFolder("file:///path/to/workspace-b", "workspace-b"),
                ],
            ),
            SphinxConfig(
                python_command=PYTHON_CMD,
                build_command=BUILD_CMD,
                python_path=PYPATH,
            ),
            None,
        ),
    ],
)
def test_resolve(
    uri: str,
    workspace: Workspace,
    config: SphinxConfig,
    expected: Optional[SphinxConfig],
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
    assert actual == expected
