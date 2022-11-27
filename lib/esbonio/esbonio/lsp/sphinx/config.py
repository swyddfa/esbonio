import hashlib
import inspect
import logging
import multiprocessing
import os
import pathlib
import re
import sys
import traceback
from types import ModuleType
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from unittest import mock

import appdirs
import pygls.uris as Uri
from pydantic import BaseModel
from pydantic import Field
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DiagnosticSeverity
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from sphinx.application import Sphinx
from sphinx.cmd.build import main as sphinx_build
from sphinx.util.logging import OnceFilter
from sphinx.util.logging import SphinxLogRecord
from sphinx.util.logging import WarningLogRecordTranslator
from typing_extensions import Literal

from esbonio.lsp.log import LOG_NAMESPACE
from esbonio.lsp.log import LspHandler
from esbonio.lsp.rst import ServerConfig

PATH_VAR_PATTERN = re.compile(r"^\${(\w+)}/?.*")
logger = logging.getLogger(LOG_NAMESPACE)


class MissingConfigError(Exception):
    """Indicates that we couldn't locate the project's 'conf.py'"""


class SphinxConfig(BaseModel):
    """Configuration values to pass to the Sphinx application instance."""

    build_dir: Optional[str] = Field(None, alias="buildDir")
    """The directory to write build outputs into."""

    builder_name: str = Field("html", alias="builderName")
    """The currently used builder name."""

    conf_dir: Optional[str] = Field(None, alias="confDir")
    """The directory containing the project's ``conf.py``."""

    config_overrides: Dict[str, Any] = Field(
        default_factory=dict, alias="configOverrides"
    )
    """Any overrides to configuration values."""

    doctree_dir: Optional[str] = Field(None, alias="doctreeDir")
    """The directory to write doctrees into."""

    force_full_build: bool = Field(False, alias="forceFullBuild")
    """Force a full build on startup."""

    keep_going: bool = Field(False, alias="keepGoing")
    """Continue building when errors (from warnings) are encountered."""

    make_mode: bool = Field(True, alias="makeMode")
    """Flag indicating if the server should align to "make mode" behavior."""

    num_jobs: Union[Literal["auto"], int] = Field(1, alias="numJobs")
    """The number of jobs to use for parallel builds."""

    quiet: bool = Field(False)
    """Hide standard Sphinx output messages"""

    silent: bool = Field(False)
    """Hide all Sphinx output."""

    src_dir: Optional[str] = Field(None, alias="srcDir")
    """The directory containing the project's source."""

    tags: List[str] = Field(default_factory=list)
    """Tags to enable during a build."""

    verbosity: int = Field(0)
    """The verbosity of Sphinx's output."""

    warning_is_error: bool = Field(False, alias="warningIsError")
    """Treat any warning as an error"""

    @property
    def parallel(self) -> int:
        """The parsed value of the ``num_jobs`` field."""

        if self.num_jobs == "auto":
            return multiprocessing.cpu_count()

        return self.num_jobs

    @classmethod
    def from_arguments(
        cls,
        *,
        cli_args: Optional[List[str]] = None,
        sphinx_args: Optional[Dict[str, Any]] = None,
    ) -> Optional["SphinxConfig"]:
        """Return the ``SphinxConfig`` instance that's equivalent to the given arguments.

        .. note::

            Only ``cli_args`` **or** ``sphinx_args`` may be given.

        .. warning::

            This method is unable to determine the value of the
            :obj:`SphinxConfig.make_mode` setting when passing ``sphinx_args``


        Parameters
        ----------
        cli_args
           The cli arguments you would normally pass to ``sphinx-build``

        sphinx_args:
           The arguments you would use to create a ``Sphinx`` application instance.
        """

        make_mode: bool = False
        neither_given = cli_args is None and sphinx_args is None
        both_given = cli_args is not None and sphinx_args is not None
        if neither_given or both_given:
            raise ValueError("You must pass either 'cli_args' or 'sphinx_args'")

        if cli_args is not None:
            # The easiest way to handle this is to just call sphinx-build but with
            # the Sphinx app object patched out - then we just use all the args it
            # was given!
            with mock.patch("sphinx.cmd.build.Sphinx") as m_Sphinx:
                sphinx_build(cli_args)

            if m_Sphinx.call_args is None:
                return None

            signature = inspect.signature(Sphinx)
            keys = signature.parameters.keys()

            values = m_Sphinx.call_args[0]
            sphinx_args = {k: v for k, v in zip(keys, values)}

            # `-M` has to be the first argument passed to `sphinx-build`
            # https://github.com/sphinx-doc/sphinx/blob/1222bed88eb29cde43a81dd208448dc903c53de2/sphinx/cmd/build.py#L287
            make_mode = cli_args[0] == "-M"
            if make_mode and sphinx_args["outdir"].endswith(sphinx_args["buildername"]):
                build_dir = pathlib.Path(sphinx_args["outdir"]).parts[:-1]
                sphinx_args["outdir"] = str(pathlib.Path(*build_dir))

        if sphinx_args is None:
            return None

        return cls(
            confDir=sphinx_args.get("confdir", None),
            configOverrides=sphinx_args.get("confoverrides", {}),
            buildDir=sphinx_args.get("outdir", None),
            builderName=sphinx_args.get("buildername", "html"),
            doctreeDir=sphinx_args.get("doctreedir", None),
            forceFullBuild=sphinx_args.get("freshenv", False),
            keepGoing=sphinx_args.get("keep_going", False),
            makeMode=make_mode,
            numJobs=sphinx_args.get("parallel", 1),
            quiet=sphinx_args.get("status", 1) is None,
            silent=sphinx_args.get("warning", 1) is None,
            srcDir=sphinx_args.get("srcdir", None),
            tags=sphinx_args.get("tags", []),
            verbosity=sphinx_args.get("verbosity", 0),
            warningIsError=sphinx_args.get("warningiserror", False),
        )

    def to_cli_args(self) -> List[str]:
        """Convert this into the equivalent ``sphinx-build`` cli arguments."""

        if self.make_mode:
            return self._build_make_cli_args()

        return self._build_cli_args()

    def _build_make_cli_args(self) -> List[str]:
        args = ["-M", self.builder_name]
        conf_dir = self.conf_dir or "${workspaceRoot}"
        src_dir = self.src_dir or conf_dir

        if self.build_dir is None:
            build_dir = pathlib.Path(src_dir, "_build")
        else:
            build_dir = pathlib.Path(self.build_dir)

        args += [src_dir, str(build_dir)]

        args += self._build_standard_args()
        default_dtree_dir = str(pathlib.Path(build_dir, "doctrees"))
        if self.doctree_dir is not None and self.doctree_dir != default_dtree_dir:
            args += ["-d", self.doctree_dir]

        return args

    def _build_cli_args(self) -> List[str]:
        args = ["-b", self.builder_name]

        conf_dir = self.conf_dir or "${workspaceRoot}"
        src_dir = self.src_dir or conf_dir

        build_dir = self.build_dir or pathlib.Path(src_dir, "_build")
        default_dtree_dir = str(pathlib.Path(build_dir, ".doctrees"))

        if self.doctree_dir is not None and self.doctree_dir != default_dtree_dir:
            args += ["-d", self.doctree_dir]

        args += self._build_standard_args()
        args += [src_dir, str(build_dir)]
        return args

    def _build_standard_args(self) -> List[str]:
        args: List[str] = []

        conf_dir = self.conf_dir or "${workspaceRoot}"
        src_dir = self.src_dir or self.conf_dir

        if conf_dir != src_dir:
            args += ["-c", conf_dir]

        if self.force_full_build:
            args += ["-E"]

        if self.parallel > 1:
            args += ["-j", str(self.num_jobs)]

        if self.silent:
            args += ["-Q"]

        if self.quiet and not self.silent:
            args += ["-q"]

        if self.warning_is_error:
            args += ["-W"]

        if self.keep_going:
            args += ["--keep-going"]

        if self.verbosity > 0:
            args += ["-" + ("v" * self.verbosity)]

        for key, value in self.config_overrides.items():

            if key == "nitpicky":
                args += ["-n"]
                continue

            if key.startswith("html_context."):
                char = "A"
                key = key.replace("html_context.", "")
            else:
                char = "D"

            args += [f"-{char}{key}={value}"]

        for tag in self.tags:
            args += ["-t", tag]

        return args

    def to_application_args(self) -> Dict[str, Any]:
        """Convert this into the equivalent Sphinx application arguments."""

        return {
            "buildername": self.builder_name,
            "confdir": self.conf_dir,
            "confoverrides": self.config_overrides,
            "doctreedir": self.doctree_dir,
            "freshenv": self.force_full_build,
            "keep_going": self.keep_going,
            "outdir": self.build_dir,
            "parallel": self.parallel,
            "srcdir": self.src_dir,
            "status": None,
            "tags": self.tags,
            "verbosity": self.verbosity,
            "warning": None,
            "warningiserror": self.warning_is_error,
        }

    def resolve(self, root_uri: str) -> "SphinxConfig":
        conf_dir = self.resolve_conf_dir(root_uri)
        if conf_dir is None:
            raise MissingConfigError()

        src_dir = self.resolve_src_dir(root_uri, str(conf_dir))
        build_dir = self.resolve_build_dir(root_uri, str(conf_dir))
        doctree_dir = self.resolve_doctree_dir(root_uri, str(conf_dir), str(build_dir))

        if self.make_mode:
            build_dir /= self.builder_name

        return SphinxConfig(
            confDir=str(conf_dir),
            configOverrides=self.config_overrides,
            buildDir=str(build_dir),
            builderName=self.builder_name,
            doctreeDir=str(doctree_dir),
            forceFullBuild=self.force_full_build,
            keepGoing=self.keep_going,
            makeMode=self.make_mode,
            numJobs=self.num_jobs,
            quiet=self.quiet,
            silent=self.silent,
            srcDir=str(src_dir),
            tags=self.tags,
            verbosity=self.verbosity,
            warningIsError=self.warning_is_error,
        )

    def resolve_build_dir(self, root_uri: str, actual_conf_dir: str) -> pathlib.Path:
        """Get the build dir to use based on the user's config.

        If nothing is specified in the given ``config``, this will choose a location
        within the user's cache dir (as determined by
        `appdirs <https://pypi.org/project/appdirs>`). The directory name will be a hash
        derived from the given ``conf_dir`` for the project.

        Alternatively the user (or least language client) can override this by setting
        either an absolute path, or a path based on the following "variables".

        - ``${workspaceRoot}`` which expands to the workspace root as provided
          by the language client.

        - ``${workspaceFolder}`` alias for ``${workspaceRoot}``, placeholder ready for
          multi-root support.

        - ``${confDir}`` which expands to the configured config dir.

        Parameters
        ----------
        root_uri
           The workspace root uri

        actual_conf_dir:
           The fully resolved conf dir for the project
        """

        if not self.build_dir:
            # Try to pick a sensible dir based on the project's location
            cache = appdirs.user_cache_dir("esbonio", "swyddfa")
            project = hashlib.md5(str(actual_conf_dir).encode()).hexdigest()

            return pathlib.Path(cache) / project

        root_dir = Uri.to_fs_path(root_uri)
        match = PATH_VAR_PATTERN.match(self.build_dir)

        if match and match.group(1) in {"workspaceRoot", "workspaceFolder"}:
            build = pathlib.Path(self.build_dir).parts[1:]
            return pathlib.Path(root_dir, *build).resolve()

        if match and match.group(1) == "confDir":
            build = pathlib.Path(self.build_dir).parts[1:]
            return pathlib.Path(actual_conf_dir, *build).resolve()

        # Convert path to/from uri so that any path quirks from windows are
        # automatically handled
        build_uri = Uri.from_fs_path(self.build_dir)
        build_dir = Uri.to_fs_path(build_uri)

        # But make sure paths starting with '~' are not corrupted
        if build_dir.startswith("/~"):
            build_dir = build_dir.replace("/~", "~")

        # But make sure (windows) paths starting with '~' are not corrupted
        if build_dir.startswith("\\~"):
            build_dir = build_dir.replace("\\~", "~")

        return pathlib.Path(build_dir).expanduser()

    def resolve_doctree_dir(
        self, root_uri: str, actual_conf_dir: str, actual_build_dir: str
    ) -> pathlib.Path:
        """Get the directory to use for doctrees based on the user's config.

        If ``doctree_dir`` is not set, this method will follow what ``sphinx-build``
        does.

        - If ``make_mode`` is true, this will be set to ``${buildDir}/doctrees``
        - If ``make_mode`` is false, this will be set to ``${buildDir}/.doctrees``

        Otherwise, if ``doctree_dir`` is set the following "variables" are handled by
        this method.

        - ``${workspaceRoot}`` which expands to the workspace root as provided by the
          language client.

        - ``${workspaceFolder}`` alias for ``${workspaceRoot}``, placeholder ready for
          multi-root support.

        - ``${confDir}`` which expands to the configured config dir.

        - ``${buildDir}`` which expands to the configured build dir.

        Parameters
        ----------
        root_uri
           The workspace root uri

        actual_conf_dir
           The fully resolved conf dir for the project

        actual_build_dir
           The fully resolved build dir for the project.
        """

        if self.doctree_dir is None:
            if self.make_mode:
                return pathlib.Path(actual_build_dir, "doctrees")

            return pathlib.Path(actual_build_dir, ".doctrees")

        root_dir = Uri.to_fs_path(root_uri)
        match = PATH_VAR_PATTERN.match(self.doctree_dir)

        if match and match.group(1) in {"workspaceRoot", "workspaceFolder"}:
            build = pathlib.Path(self.doctree_dir).parts[1:]
            return pathlib.Path(root_dir, *build).resolve()

        if match and match.group(1) == "confDir":
            build = pathlib.Path(self.doctree_dir).parts[1:]
            return pathlib.Path(actual_conf_dir, *build).resolve()

        if match and match.group(1) == "buildDir":
            build = pathlib.Path(self.doctree_dir).parts[1:]
            return pathlib.Path(actual_build_dir, *build).resolve()

        return pathlib.Path(self.doctree_dir).expanduser()

    def resolve_conf_dir(self, root_uri: str) -> Optional[pathlib.Path]:
        """Get the conf dir to use based on the user's config.

        If ``conf_dir`` is not set, this method will attempt to find it by searching
        within the ``root_uri`` for a ``conf.py`` file. If multiple files are found, the
        first one found will be chosen.

        If ``conf_dir`` is set the following "variables" are handled by this method

        - ``${workspaceRoot}`` which expands to the workspace root as provided by the
          language client.

        - ``${workspaceFolder}`` alias for ``${workspaceRoot}``, placeholder ready for
          multi-root support.

        Parameters
        ----------
        root_uri
            The workspace root uri
        """
        root = Uri.to_fs_path(root_uri)

        if not self.conf_dir:
            ignore_paths = [".tox", "site-packages"]

            for candidate in pathlib.Path(root).glob("**/conf.py"):
                # Skip any files that obviously aren't part of the project
                if any(path in str(candidate) for path in ignore_paths):
                    continue

                return candidate.parent

            # Nothing found
            return None

        match = PATH_VAR_PATTERN.match(self.conf_dir)
        if not match or match.group(1) not in {"workspaceRoot", "workspaceFolder"}:
            return pathlib.Path(self.conf_dir).expanduser()

        conf = pathlib.Path(self.conf_dir).parts[1:]
        return pathlib.Path(root, *conf).resolve()

    def resolve_src_dir(self, root_uri: str, actual_conf_dir: str) -> pathlib.Path:
        """Get the src dir to use based on the user's config.

        By default the src dir will be the same as the conf dir, but this can
        be overriden by setting the ``src_dir`` field.

        There are a number of "variables" that can be included in the path,
        currently we support

        - ``${workspaceRoot}`` which expands to the workspace root as provided
          by the language client.

        - ``${workspaceFolder}`` alias for ``${workspaceRoot}``, placeholder ready for
          multi-root support.

        - ``${confDir}`` which expands to the configured config dir.

        Parameters
        ----------
        root_uri
           The workspace root uri

        actual_conf_dir
           The fully resolved conf dir for the project
        """

        if not self.src_dir:
            return pathlib.Path(actual_conf_dir)

        src_dir = self.src_dir
        root_dir = Uri.to_fs_path(root_uri)

        match = PATH_VAR_PATTERN.match(src_dir)
        if match and match.group(1) in {"workspaceRoot", "workspaceFolder"}:
            src = pathlib.Path(src_dir).parts[1:]
            return pathlib.Path(root_dir, *src).resolve()

        if match and match.group(1) == "confDir":
            src = pathlib.Path(src_dir).parts[1:]
            return pathlib.Path(actual_conf_dir, *src).resolve()

        return pathlib.Path(src_dir).expanduser()


class SphinxServerConfig(ServerConfig):
    """
    .. deprecated:: 0.12.0

       This will be removed in v1.0.
       Use :confval:`sphinx.quiet (boolean)` and :confval:`sphinx.silent (boolean)`
       options instead.
    """

    hide_sphinx_output: bool = Field(False, alias="hideSphinxOutput")
    """A flag to indicate if Sphinx build output should be omitted from the log."""


class InitializationOptions(BaseModel):
    """The initialization options we can expect to receive from a client."""

    sphinx: SphinxConfig = Field(default_factory=SphinxConfig)
    """The ``esbonio.sphinx.*`` namespace of options."""

    server: SphinxServerConfig = Field(default_factory=SphinxServerConfig)
    """The ``esbonio.server.*`` namespace of options."""


DIAGNOSTIC_SEVERITY = {
    logging.ERROR: DiagnosticSeverity.Error,
    logging.INFO: DiagnosticSeverity.Information,
    logging.WARNING: DiagnosticSeverity.Warning,
}


class SphinxLogHandler(LspHandler):
    """A logging handler that can extract errors from Sphinx's build output."""

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = app
        self.translator = WarningLogRecordTranslator(app)
        self.only_once = OnceFilter()
        self.diagnostics: Dict[str, List[Diagnostic]] = {}

    def get_location(self, location: str) -> Tuple[str, Optional[int]]:

        if not location:
            conf = pathlib.Path(self.app.confdir, "conf.py")
            return (Uri.from_fs_path(str(conf)), None)

        lineno = None
        path, parts = self.get_location_path(location)

        if len(parts) == 1:
            try:
                lineno = int(parts[0])
            except ValueError:
                pass

        if len(parts) == 2 and parts[0].startswith("docstring of "):
            target = parts[0].replace("docstring of ", "")
            lineno = self.get_docstring_location(target, parts[1])

        return (Uri.from_fs_path(path), lineno)

    def get_location_path(self, location: str) -> Tuple[str, List[str]]:
        """Determine the filepath from the given location."""

        if location.startswith("internal padding before "):
            location = location.replace("internal padding before ", "")

        if location.startswith("internal padding after "):
            location = location.replace("internal padding after ", "")

        path, *parts = location.split(":")

        # On windows the rest of the path will be the first element of parts
        if pathlib.Path(location).drive:
            path += f":{parts.pop(0)}"

        # Diagnostics in .. included:: files are reported relative to the process'
        # working directory, so ensure the path is absolute.
        path = os.path.abspath(path)

        return path, parts

    def get_docstring_location(self, target: str, offset: str) -> Optional[int]:

        # The containing module will be the longest substring we can find in target
        candidates = [m for m in sys.modules.keys() if target.startswith(m)] + [""]
        module = sys.modules.get(sorted(candidates, key=len, reverse=True)[0], None)

        if module is None:
            return None

        obj: Union[ModuleType, Any, None] = module
        dotted_name = target.replace(module.__name__ + ".", "")

        for name in dotted_name.split("."):
            obj = getattr(obj, name, None)
            if obj is None:
                return None

        try:
            _, line = inspect.getsourcelines(obj)  # type: ignore

            # Correct off by one error for docstrings that don't start with a newline.
            nl = (obj.__doc__ or "").startswith("\n")
            return line + int(offset) - (not nl)
        except Exception:
            logger.debug(
                "Unable to determine diagnostic location\n%s", traceback.format_exc()
            )
            return None

    def emit(self, record: logging.LogRecord) -> None:

        conditions = [
            "sphinx" not in record.name,
            record.levelno not in {logging.WARNING, logging.ERROR},
            not self.translator,
        ]

        if any(conditions):
            # Log the record as normal
            super().emit(record)
            return

        # Only process errors/warnings once.
        if not self.only_once.filter(record):
            return

        # Let sphinx do what it does to warning/error messages
        self.translator.filter(record)  # type: ignore

        loc = record.location if isinstance(record, SphinxLogRecord) else ""
        doc, lineno = self.get_location(loc)
        line = lineno or 1
        logger.debug("Reporting diagnostic at %s:%s", doc, line)

        try:
            # Not every message contains a string...
            if not isinstance(record.msg, str):
                message = str(record.msg)
            else:
                message = record.msg

            # Only attempt to format args if there are args to format
            if record.args is not None and len(record.args) > 0:
                message = message % record.args

        except Exception:
            message = str(record.msg)
            logger.error(
                "Unable to format diagnostic message: %s", traceback.format_exc()
            )

        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=line - 1, character=0),
                end=Position(line=line, character=0),
            ),
            message=message,
            severity=DIAGNOSTIC_SEVERITY.get(
                record.levelno, DiagnosticSeverity.Warning
            ),
        )

        if doc not in self.diagnostics:
            self.diagnostics[doc] = [diagnostic]
        else:
            self.diagnostics[doc].append(diagnostic)

        super().emit(record)
