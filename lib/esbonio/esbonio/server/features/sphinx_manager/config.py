from __future__ import annotations

import importlib.util
import json
import logging
import os
import pathlib
import re
import sys
from typing import Any

import attrs
from pygls import IS_WIN
from pygls.workspace import Workspace

from esbonio.server import Uri

VARIABLE = re.compile(r"\$\{([^}]+)\}")


def get_module_path(module: str) -> pathlib.Path | None:
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
class SubProcess:
    """Captures the information necessary to spawn the Sphinx agent subprocess"""

    command: list[str] = attrs.field(factory=list)
    """The command to invoke, plus any additional arguments."""

    env: dict[str, str] = attrs.field(factory=dict)
    """Additional environment variables to set for the process."""

    cwd: str = attrs.field(default="${scopeFsPath}")
    """The working directory to use."""

    def resolve(
        self, uri: Uri, workspace: Workspace, logger: logging.Logger
    ) -> SubProcess | None:
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
        SubProcess | None
           The fully resolved config object to use.
           If ``None``, a valid configuration could not be created.
        """
        if (cwd := self._resolve_cwd(uri, workspace, logger)) is None:
            return None

        logger.debug("cwd: %s", cwd)
        if len(command := self._resolve_python(logger, cwd)) == 0:
            return None

        if (env := self._resolve_env(logger)) is None:
            return None

        return SubProcess(command=command, env=env, cwd=cwd)

    def _resolve_python(self, logger: logging.Logger, cwd: str) -> list[str]:
        """Return the python command to use when launching the sphinx agent.

        This could be as simple as the path to the python interpreter in a
        particular virtual environment or a complex command such as
        ``hatch -e docs run python``.

        If the user has not configured a python command, this will fallback to
        using ``sys.executable``.

        Parameters
        ----------
        logger
           The logger instance to use

        Returns
        -------
        list[str]
           The command to use when invoking python
        """
        if len(command := list(self.command)) == 0:
            logger.warning(
                "No pythonCommand configured! Reusing the server's environment."
            )
            return [sys.executable]

        command = [_resolve_variable(c, cwd) for c in command]
        return command

    def _resolve_env(self, logger: logging.Logger) -> dict[str, str] | None:
        """Construct the environment variables to set for the process.

        Using the ``PYTHONPATH`` environment variable, we can inject additional Python
        packages into the user's Python environment. This method locates the
        installation path of the sphinx agent and ensures it's added to the front
        of the ``PYTHONPATH`` variable.

        Parameters
        ----------
        logger
           The logger instance to use

        Returns
        -------
        dict[str, str]
           The environment variables to use.
        """

        if (sphinx_agent := get_module_path("esbonio.sphinx_agent")) is None:
            logger.error("Unable to locate the `esbonio.sphinx_agent` module")
            return None

        python_path: list[pathlib.Path | str] = [sphinx_agent]

        if len(pypath := self.env.get("PYTHONPATH", "")) > 0:
            python_path.append(pypath)

        env = {
            **self.env,
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": os.pathsep.join(str(p) for p in python_path),
        }

        # Only log the environment variables set *before* copying in the wider
        # environment
        logger.debug("env: %s", json.dumps(env, indent=2))
        for envname, value in os.environ.items():
            # Don't pass any vars we've explictly set.
            if envname in env:
                continue

            env[envname] = value

        return env

    def _resolve_cwd(
        self, uri: Uri, workspace: Workspace, logger: logging.Logger
    ) -> str | None:
        """Determine the working directory from which to launch the Sphinx agent.

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
        logger.debug(f"{self.cwd}")
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
                        "Unable to determine working directory from %r", folder
                    )
                    return None

                return cwd

        return None


@attrs.define
class SphinxConfig:
    """Configuration for the sphinx agent subprocess."""

    enable_dev_tools: bool = attrs.field(default=False)
    """Flag to enable dev tools."""

    python_command: SubProcess = attrs.field(factory=SubProcess)
    """The command to use when launching the python interpreter."""

    build_command: list[str] = attrs.field(factory=list)
    """The sphinx-build command to use."""

    config_overrides: dict[str, Any] = attrs.field(factory=dict)
    """Overrides to apply to Sphinx's configuration."""

    @property
    def sphinx_command(self) -> SubProcess:
        """Return the command definition necessary to launch the sphinx agent."""
        command: list[str] = []
        python = self.python_command

        if len(python.command) == 0:
            raise ValueError("No python environment configured")

        if self.enable_dev_tools:
            command.extend(["lsp-devtools", "agent", "--"])

        command.extend([*python.command, "-m", "sphinx_agent"])
        return SubProcess(command=command, env=python.env, cwd=python.cwd)

    def resolve(
        self,
        uri: Uri,
        workspace: Workspace,
        logger: logging.Logger,
    ) -> SphinxConfig | None:
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
        python_command = self.python_command.resolve(uri, workspace, logger)
        if python_command is None:
            return None

        build_command = self._resolve_build_command(uri, logger)
        if len(build_command) == 0:
            return None

        logger.debug("Build command: %r", build_command)

        return SphinxConfig(
            enable_dev_tools=self.enable_dev_tools,
            config_overrides=self.config_overrides,
            python_command=python_command,
            build_command=build_command,
        )

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
