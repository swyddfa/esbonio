from __future__ import annotations

import importlib.util
import logging
import os
import pathlib
import re
import sys
from typing import Any
from typing import Optional

import attrs
from pygls import IS_WIN
from pygls.workspace import Workspace

from esbonio.server import Uri

VARIABLE = re.compile(r"\$\{([^}]+)\}")


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

    python_command: list[str] = attrs.field(factory=list)
    """The command to use when launching the python interpreter."""

    build_command: list[str] = attrs.field(factory=list)
    """The sphinx-build command to use."""

    config_overrides: dict[str, Any] = attrs.field(factory=dict)
    """Overrides to apply to Sphinx's configuration."""

    env_passthrough: list[str] = attrs.field(factory=list)
    """List of environment variables to pass through to the Sphinx subprocess"""

    cwd: str = attrs.field(default="${scopeFsPath}")
    """The working directory to use."""

    # Unable to use `str | None` syntax with cattrs when running Python 3.9
    fallback_env: Optional[str] = attrs.field(default=None)
    """Location of the fallback environment to use.

    Intended to be used by clients to handle the case where the user has not configured
    ``python_command`` themselves."""

    python_path: list[pathlib.Path] = attrs.field(factory=list)
    """The value of ``PYTHONPATH`` to use when injecting the sphinx agent into the
    target environment"""

    def resolve(
        self,
        uri: Uri,
        workspace: Workspace,
        logger: logging.Logger,
    ) -> Optional[SphinxConfig]:
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

        if (cwd := self._resolve_cwd(uri, workspace, logger)) is None:
            return None

        python_command, python_path = self._resolve_python(logger, cwd)
        if len(python_path) == 0 or len(python_command) == 0:
            return None

        build_command = self._resolve_build_command(uri, logger)
        if len(build_command) == 0:
            return None

        logger.debug("Cwd: %s", cwd)
        logger.debug("Build command: %s", build_command)

        return SphinxConfig(
            enable_dev_tools=self.enable_dev_tools,
            config_overrides=self.config_overrides,
            cwd=cwd,
            env_passthrough=self.env_passthrough,
            python_command=python_command,
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

    def _resolve_python(
        self, logger: logging.Logger, cwd: str
    ) -> tuple[list[str], list[pathlib.Path]]:
        """Return the python configuration to use when launching the sphinx agent.

        The first element of the returned tuple is the command to use when running the
        sphinx agent. This could be as simple as the path to the python interpreter in a
        particular virtual environment or a complex command such as
        ``hatch -e docs run python``.

        Using the ``PYTHONPATH`` environment variable, we can inject additional Python
        packages into the user's Python environment. This method also locates the
        installation path of the sphinx agent and returns it in the second element of the
        tuple.

        Finally, if the user has not configured a python environment and the client has
        set the ``fallback_env`` option, this method will construct a command based on
        the current interpreter to create an isolated environment based on
        ``fallback_env``.

        Parameters
        ----------
        logger
           The logger instance to use

        Returns
        -------
        tuple[list[str], list[pathlib.Path]]
           A tuple of the form ``(python_command, python_path)``.
        """
        if len(python_path := list(self.python_path)) == 0:
            if (sphinx_agent := get_module_path("esbonio.sphinx_agent")) is None:
                logger.error("Unable to locate the sphinx agent")
                return [], []

            python_path.append(sphinx_agent)

        if len(python_command := list(self.python_command)) == 0:
            if self.fallback_env is None:
                logger.error("No python command configured")
                return [], []

            if not (fallback_env := pathlib.Path(self.fallback_env)).exists():
                logger.error(
                    "Provided fallback environment %s does not exist", fallback_env
                )
                return [], []

            # Since the client has provided a fallback environment we can isolate the
            # current Python interpreter from its environment and reuse it.
            logger.debug("Using fallback environment")
            python_path.append(fallback_env)
            python_command.extend([sys.executable, "-S"])

        else:
            python_command = [_resolve_variable(c, cwd) for c in python_command]

        return python_command, python_path

    def _resolve_build_command(self, uri: Uri, logger: logging.Logger) -> list[str]:
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
                return [
                    "sphinx-build",
                    "-M",
                    "dirhtml",
                    str(current),
                    "${defaultBuildDir}",
                ]

        return []


def _resolve_variable(arg: str, cwd: str) -> str:
    """Resolve the configuration variables in the given argument, if any.

    Parameters
    ----------
    arg
       The string containing the vatiables to resolve

    cwd
       The current working directory of the configuration.
    """

    if (match := VARIABLE.match(arg)) is None:
        return arg

    varname = match.group(1)

    if varname.startswith("venv:"):
        env = varname.replace("venv:", "")
        return _resolve_variable_venv(env, cwd)

    raise ValueError(f"Undefined variable: {varname!r}")


def _resolve_variable_venv(env: str, cwd: str) -> str:
    """Resolve the ``${venv:<path>}`` config variable"""
    if IS_WIN:
        envpath = pathlib.Path(env, "Scripts", "python.exe")
    else:
        envpath = pathlib.Path(env, "bin", "python")

    if envpath.is_absolute():
        return str(envpath)
    else:
        envpath = cwd / envpath
        # Can't call envpath.resolve() here as that will also follow symlinks which we
        # don't want to do
        # https://github.com/swyddfa/esbonio/issues/945
        return os.path.normpath(envpath)
