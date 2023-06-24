import hashlib
import importlib.util
import logging
import pathlib
from typing import List
from typing import Optional

import appdirs
import attrs
import pygls.uris as Uri
from pygls.workspace import Workspace


def get_python_path(module: str) -> Optional[pathlib.Path]:
    spec = importlib.util.find_spec(module)
    if spec is None:
        return None

    if spec.origin is None:
        return None

    # origin = .../esbonio/sphinx_agent/__init__.py
    agent = pathlib.Path(spec.origin)
    return agent.parent.parent


@attrs.define
class SphinxConfig:
    """Configuration for the sphinx application instance."""

    enable_dev_tools: bool = attrs.field(default=False)
    """Flag to enable dev tools."""

    enable_sync_scrolling: bool = attrs.field(default=True)
    """Flag to enable sync scrolling."""

    python_command: List[str] = attrs.field(factory=list)
    """The command to use when launching the python interpreter."""

    build_command: List[str] = attrs.field(factory=list)
    """The sphinx-build command to use."""

    cwd: str = attrs.field(default="")
    """The working directory to use."""

    python_path: List[pathlib.Path] = attrs.field(factory=list)
    """The value of ``PYTHONPATH`` to use when injecting the sphinx agent into the
    target environment"""

    def resolve(
        self,
        uri: str,
        workspace: Workspace,
        logger: logging.Logger,
    ) -> "Optional[SphinxConfig]":
        """Resolve the configuration based on user provided values."""

        if len(self.python_path) == 0:
            if (python_path := self._resolve_python_path(logger)) is None:
                return None

            self.python_path = python_path

        cwd = self._resolve_cwd(uri, workspace, logger)
        if cwd is None:
            return None

        build_command = self.build_command
        if len(build_command) == 0:
            build_command = self._guess_build_command(uri, logger)

        return SphinxConfig(
            enable_dev_tools=self.enable_dev_tools,
            enable_sync_scrolling=self.enable_sync_scrolling,
            cwd=cwd,
            python_command=self.python_command,
            build_command=build_command,
            python_path=self.python_path,
        )

    def _resolve_cwd(self, uri: str, workspace: Workspace, logger: logging.Logger):
        for folder_uri in workspace.folders.keys():
            if uri.startswith(folder_uri):
                break
        else:
            folder_uri = workspace.root_uri

        cwd = Uri.to_fs_path(folder_uri)
        if cwd is None:
            logger.error("Unable to determine working directory from '%s'", folder_uri)
            return None

        logger.debug("Cwd: %s", cwd)
        return cwd

    def _resolve_python_path(
        self, logger: logging.Logger
    ) -> Optional[List[pathlib.Path]]:
        if (sphinx_agent := get_python_path("esbonio.sphinx_agent")) is None:
            logger.error("Unable to locate the sphinx agent")
            return None

        python_path = [sphinx_agent]
        if self.enable_dev_tools:
            if (lsp_devtools := get_python_path("lsp_devtools")) is None:
                logger.warning(
                    "Unable to locate module 'lsp_devtools', dev tools will not "
                    "be availble."
                )
            else:
                python_path.append(lsp_devtools)

        return python_path

    def _guess_build_command(self, uri: str, logger: logging.Logger) -> List[str]:
        """Try and guess something a sensible build command given the uri."""

        path = Uri.to_fs_path(uri)
        if path is None:
            return []

        # Search upwards from the given uri to see if we find something that looks like
        # a sphinx conf.py file.
        previous = None
        current = pathlib.Path(path)

        while previous != current:
            previous = current
            current = previous.parent

            conf_py = current / "conf.py"
            logger.debug("Trying path: %s", current)
            if conf_py.exists():
                cache = appdirs.user_cache_dir("esbonio", "swyddfa")
                project = hashlib.md5(str(current).encode()).hexdigest()
                build_dir = str(pathlib.Path(cache, project))
                return ["sphinx-build", "-M", "dirhtml", str(current), str(build_dir)]

        return []
