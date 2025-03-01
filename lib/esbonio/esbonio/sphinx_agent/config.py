from __future__ import annotations

import dataclasses
import hashlib
import inspect
import pathlib
import re
import sys
from typing import Any
from typing import Literal
from typing import Optional
from typing import Union
from unittest import mock

from sphinx.application import Sphinx
from sphinx.cmd.build import main as sphinx_build

VARIABLE = re.compile(r"\$\{(\w+)\}")


@dataclasses.dataclass
class SphinxConfig:
    """Configuration values to pass to the Sphinx application instance."""

    src_dir: str
    """The directory containing the project's source."""

    conf_dir: str
    """The directory containing the project's ``conf.py``."""

    build_dir: str
    """The directory to write build outputs into."""

    builder_name: str
    """The currently used builder name."""

    doctree_dir: str
    """The directory to write doctrees into."""

    config_overrides: dict[str, Any] = dataclasses.field(default_factory=dict)
    """Any overrides to configuration values."""

    force_full_build: bool = dataclasses.field(default=False)
    """Force a full build on startup."""

    keep_going: bool = dataclasses.field(default=False)
    """Continue building when errors (from warnings) are encountered."""

    num_jobs: Union[Literal["auto"], int] = dataclasses.field(default=1)
    """The number of jobs to use for parallel builds."""

    quiet: bool = dataclasses.field(default=False)
    """Hide standard Sphinx output messages"""

    silent: bool = dataclasses.field(default=False)
    """Hide all Sphinx output."""

    tags: list[str] = dataclasses.field(default_factory=list)
    """Tags to enable during a build."""

    verbosity: int = dataclasses.field(default=0)
    """The verbosity of Sphinx's output."""

    version: Optional[str] = dataclasses.field(default=None)
    """Sphinx's version number."""

    warning_is_error: bool = dataclasses.field(default=False)
    """Treat any warning as an error"""

    @property
    def parallel(self) -> int:
        """The parsed value of the ``num_jobs`` field."""

        if self.num_jobs == "auto":
            import multiprocessing

            return multiprocessing.cpu_count()

        return self.num_jobs

    @classmethod
    def fromcli(cls, args: list[str]):
        """Return the ``SphinxConfig`` instance that's equivalent to the given arguments.

        Parameters
        ----------
        args
           The cli arguments you would normally pass to ``sphinx-build``

        Returns
        -------
        Optional[SphinxConfig]
           ``None`` if the arguments could not be parsed, otherwise the set configuration
           options derived from the sphinx build command.
        """

        if args[0] == "sphinx-build":
            args = args[1:]

        # The easiest way to handle this is to just call sphinx-build but with
        # the Sphinx app object patched out - then we just use all the args it
        # was given!
        with mock.patch("sphinx.cmd.build.Sphinx") as m_Sphinx:
            sphinx_build(args)

        if m_Sphinx.call_args is None:
            return None

        signature = inspect.signature(Sphinx)
        keys = signature.parameters.keys()

        values = m_Sphinx.call_args[0]
        sphinx_args = {k: v for k, v in zip(keys, values)}

        # Sphinx 8.1 changed the way arguments are passed to the `Sphinx` class.
        # See: https://github.com/swyddfa/esbonio/issues/912
        if len(values) == 0:
            sphinx_args = m_Sphinx.call_args.kwargs

        if sphinx_args is None:
            return None

        return cls(
            src_dir=sphinx_args["srcdir"],
            conf_dir=sphinx_args["confdir"],
            build_dir=sphinx_args["outdir"],
            builder_name=sphinx_args["buildername"],
            doctree_dir=sphinx_args["doctreedir"],
            config_overrides=sphinx_args.get("confoverrides", {}),
            force_full_build=sphinx_args.get("freshenv", False),
            keep_going=sphinx_args.get("keep_going", False),
            num_jobs=sphinx_args.get("parallel", 1),
            quiet=sphinx_args.get("status", 1) is None,
            silent=sphinx_args.get("warning", 1) is None,
            tags=sphinx_args.get("tags", []),
            verbosity=sphinx_args.get("verbosity", 0),
            warning_is_error=sphinx_args.get("warningiserror", False),
        )

    def to_application_args(self, context: dict[str, Any]) -> dict[str, Any]:
        """Convert this into the equivalent Sphinx application arguments."""

        # On OSes like Fedora Silverblue, `/home` is symlinked to `/var/home`.  This
        # causes issues, since, depending on the origin of any path given to us `/home`
        # may or may not be the true location of the file - which introduces consistency
        # problems throughout the codebase.
        #
        # Resolving these paths here, should ensure that the agent always
        # reports the true location of any given directory.
        conf_dir = pathlib.Path(self.conf_dir).resolve()
        self.conf_dir = str(conf_dir)

        # Resolve any config variables.
        #
        # This is a bit hacky, but let's go with it for now. The only config variable
        # we currently support is 'defaultBuildDir' which is derived from the value
        # of `conf_dir`. So we resolve the full path of `conf_dir` above, then resolve
        # the configuration variables here, before finally calling resolve() on the
        # remaining paths below.
        for name, value in dataclasses.asdict(self).items():
            # value can sometimes be Sphinx's `_StrPath` helper
            value = str(value)
            if (match := VARIABLE.match(value)) is None:
                continue

            replacement = self.resolve_config_variable(match.group(1), context)
            result = VARIABLE.sub(replacement.replace("\\", r"\\"), value)

            setattr(self, name, result)

        build_dir = pathlib.Path(self.build_dir).resolve()
        doctree_dir = pathlib.Path(self.doctree_dir).resolve()
        src_dir = pathlib.Path(self.src_dir).resolve()

        return {
            "buildername": self.builder_name,
            "confdir": str(conf_dir),
            "confoverrides": self.config_overrides,
            "doctreedir": str(doctree_dir),
            "freshenv": self.force_full_build,
            "keep_going": self.keep_going,
            "outdir": str(build_dir),
            "parallel": self.parallel,
            "srcdir": str(src_dir),
            "status": sys.stderr,
            "tags": self.tags,
            "verbosity": self.verbosity,
            "warning": sys.stderr,
            "warningiserror": self.warning_is_error,
        }

    def resolve_config_variable(self, name: str, context: dict[str, str]):
        """Resolve the value for the given configuration variable."""

        if name.lower() == "defaultbuilddir":
            if (cache_dir := context.get("cacheDir")) is None:
                raise RuntimeError(
                    f"Unable to resolve config variable {name!r}, "
                    "missing context value: 'cacheDir'"
                )

            project = hashlib.md5(self.conf_dir.encode()).hexdigest()  # noqa: S324
            return str(pathlib.Path(cache_dir, project))

        raise ValueError(f"Unknown configuration variable {name!r}")
