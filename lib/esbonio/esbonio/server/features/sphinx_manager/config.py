import hashlib
import importlib.util
import logging
import pathlib
from typing import List
from typing import Optional

import attrs
import platformdirs
from pygls.workspace import Workspace

from esbonio.server import Uri


def get_module_path(module: str) -> Optional[pathlib.Path]:
    """Return the path to the directory containing the given module name.

    Parameters
    ----------
    module
       A valid Python module name e.g. ``esbonio.sphinx_agent``

    Returns
    -------
    pathlib.Path | None
       The path to the directory containing the given module.
       If ``None``, the module could not be found.
    """
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
    """Configuration for the sphinx agent subprocess."""

    enable_dev_tools: bool = attrs.field(default=False)
    """Flag to enable dev tools."""

    python_command: List[str] = attrs.field(factory=list)
    """The command to use when launching the python interpreter."""

    build_command: List[str] = attrs.field(factory=list)
    """The sphinx-build command to use."""

    env_passthrough: List[str] = attrs.field(factory=list)
    """List of environment variables to pass through to the Sphinx subprocess"""

    cwd: str = attrs.field(default="${scopeFsPath}")
    """The working directory to use."""

    python_path: List[pathlib.Path] = attrs.field(factory=list)
    """The value of ``PYTHONPATH`` to use when injecting the sphinx agent into the
    target environment"""

    def resolve(
        self,
        uri: Uri,
        workspace: Workspace,
        logger: logging.Logger,
    ) -> "Optional[SphinxConfig]":
        """Resolve the configuration based on user provided values.

        Parameters
        ----------
        uri
           The uri of the file we are creating the sphinx agent instace for

        workspace
           The user's workspace

        logger
           The logger instance to use.

        Returns
        -------
        SphinxConfig | None
           The fully resolved config object to use.
           If ``None``, a valid configuration could not be created.
        """
        python_path = self._resolve_python_path(logger)
        if len(python_path) == 0:
            return None

        cwd = self._resolve_cwd(uri, workspace, logger)
        if cwd is None:
            return None

        build_command = self._resolve_build_command(uri, logger)
        if len(build_command) == 0:
            return None

        logger.debug("Cwd: %s", cwd)
        logger.debug("Build command: %s", build_command)

        return SphinxConfig(
            enable_dev_tools=self.enable_dev_tools,
            cwd=cwd,
            env_passthrough=self.env_passthrough,
            python_command=self.python_command,
            build_command=build_command,
            python_path=python_path,
        )

    def _resolve_cwd(
        self, uri: Uri, workspace: Workspace, logger: logging.Logger
    ) -> Optional[str]:
        """If no working directory is given, try to determine the appropriate working
        directory based on the workspace.

        Parameters
        ----------
        uri
           The uri of the file we are creating an agent instance for

        workspace
           The user's workspace.

        logger
           The logger instance to use.

        Returns
        -------
        str | None
           The working directory to launch the sphinx agent in.
           If ``None``, the working directory could not be determined.
        """
        if self.cwd and self.cwd != "${scopeFsPath}":
            return self.cwd

        candidates = [Uri.parse(f) for f in workspace.folders.keys()]

        if workspace.root_uri is not None:
            if (root_uri := Uri.parse(workspace.root_uri)) not in candidates:
                candidates.append(root_uri)

        for folder in candidates:
            if str(uri).startswith(str(folder)):
                if (cwd := folder.fs_path) is None:
                    logger.error(
                        "Unable to determine working directory from '%s'", folder
                    )
                    return None

                return cwd

        return None

    def _resolve_python_path(self, logger: logging.Logger) -> List[pathlib.Path]:
        """Return the list of paths to put on the sphinx agent's ``PYTHONPATH``

        Using the ``PYTHONPATH`` environment variable, we can inject additional Python
        packages into the user's Python environment. This method will locate the
        installation path of the sphinx agent and return it.

        Parameters
        ----------
        logger
           The logger instance to use

        Returns
        -------
        List[pathlib.Path]
           The list of paths to Python packages to inject into the sphinx agent's target
           environment. If empty, the ``esbonio.sphinx_agent`` package was not found.
        """
        if len(self.python_path) > 0:
            return self.python_path

        if (sphinx_agent := get_module_path("esbonio.sphinx_agent")) is None:
            logger.error("Unable to locate the sphinx agent")
            return []

        python_path = [sphinx_agent]
        return python_path

    def _resolve_build_command(self, uri: Uri, logger: logging.Logger) -> List[str]:
        """Return the ``sphinx-build`` command to use.

        If no command is configured, this will attempt to guess the command to use based
        on the user's workspace.

        Parameters
        ----------
        uri
           The uri of the file we are creating the sphinx agent for.

        logger
           The logger instance to use.

        Returns
        -------
        List[str]
           The ``sphinx-build`` command to use.
           If empty, no build command could be determined.
        """

        if len(self.build_command) > 0:
            return self.build_command

        if (path := uri.fs_path) is None:
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
                cache = platformdirs.user_cache_dir("esbonio", "swyddfa")
                project = hashlib.md5(str(current).encode()).hexdigest()  # noqa: S324
                build_dir = str(pathlib.Path(cache, project))
                return ["sphinx-build", "-M", "dirhtml", str(current), str(build_dir)]

        return []
