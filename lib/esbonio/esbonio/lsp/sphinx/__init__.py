import hashlib
import json
import logging
import multiprocessing
import pathlib
import platform
import re
import traceback
import typing
from multiprocessing import Process
from multiprocessing import Queue
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import appdirs
import pygls.uris as Uri
from docutils.parsers.rst import Directive
from pydantic import BaseModel
from pydantic import Field
from pygls import IS_WIN
from pygls.lsp.types import DeleteFilesParams
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DiagnosticSeverity
from pygls.lsp.types import DidSaveTextDocumentParams
from pygls.lsp.types import InitializedParams
from pygls.lsp.types import InitializeParams
from pygls.lsp.types import MessageType
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import ShowDocumentParams
from sphinx import __version__ as __sphinx_version__
from sphinx.application import Sphinx
from sphinx.domains import Domain
from sphinx.errors import ConfigError
from sphinx.util import console
from sphinx.util.logging import SphinxLogRecord
from sphinx.util.logging import WarningLogRecordTranslator
from typing_extensions import Literal

from esbonio.cli import setup_cli
from esbonio.lsp.rst import LspHandler
from esbonio.lsp.rst import RstLanguageServer
from esbonio.lsp.rst import ServerConfig
from esbonio.lsp.sphinx.preview import make_preview_server
from esbonio.lsp.sphinx.preview import start_preview_server

try:
    from sphinx.util.logging import OnceFilter
except ImportError:
    # OnceFilter is not defined in Sphinx 2.x
    class OnceFilter:  # type: ignore
        def filter(self, *args, **kwargs):
            return True


IS_LINUX = platform.system() == "Linux"

# fmt: off
# Order matters!
DEFAULT_MODULES = [
    "esbonio.lsp.directives",         # Generic directive support
    "esbonio.lsp.roles",              # Generic roles support
    "esbonio.lsp.sphinx.codeblocks",  # Support for code-block, highlight, etc.
    "esbonio.lsp.sphinx.domains",     # Support for Sphinx domains
    "esbonio.lsp.sphinx.images",      # Support for image, figure etc
    "esbonio.lsp.sphinx.includes",    # Support for include, literal-include etc.
    "esbonio.lsp.sphinx.roles",       # Support for misc roles added by Sphinx e.g. :download:
]
"""The modules to load in the default configuration of the server."""
# fmt: on

DIAGNOSTIC_SEVERITY = {
    logging.ERROR: DiagnosticSeverity.Error,
    logging.INFO: DiagnosticSeverity.Information,
    logging.WARNING: DiagnosticSeverity.Warning,
}

PATH_VAR_PATTERN = re.compile(r"^\${(\w+)}/?.*")


class MissingConfigError(Exception):
    """Indicates that we couldn't locate the project's 'conf.py'"""


class SphinxConfig(BaseModel):
    """Used to represent either the current Sphinx configuration or the config options
    provided by the user at startup.
    """

    version: Optional[str]
    """Sphinx's version number."""

    conf_dir: Optional[str] = Field(None, alias="confDir")
    """Can be used to override the default conf.py discovery mechanism."""

    src_dir: Optional[str] = Field(None, alias="srcDir")
    """Can be used to override the default assumption on where the project's rst files
    are located."""

    build_dir: Optional[str] = Field(None, alias="buildDir")
    """Can be used to override the default location for storing build outputs."""

    builder_name: str = Field("html", alias="builderName")
    """The currently used builder name."""

    force_full_build: bool = Field(True, alias="forceFullBuild")
    """Flag that can be used to force a full build on startup."""

    num_jobs: Union[Literal["auto"], int] = Field("auto", alias="numJobs")
    """The number of jobs to use for parallel builds."""

    @property
    def parallel(self) -> int:
        """The parsed value of the ``num_jobs`` field."""

        if self.num_jobs == "auto":
            return multiprocessing.cpu_count()

        return self.num_jobs

    def get_sphinx_args(self, root_uri: str) -> Dict[str, Any]:
        """Get the arguments for the Sphinx application object corresponding to this
        config.

        Parameters
        ----------
        root_uri
           The workspace root uri

        Raises
        ------
        MissingConfigError
           Raised when a valid conf dir cannot be found.
        """

        conf_dir = self.resolve_conf_dir(root_uri)
        if conf_dir is None:
            raise MissingConfigError()

        builder_name = self.builder_name
        src_dir = self.resolve_src_dir(root_uri, str(conf_dir))
        build_dir = self.resolve_build_dir(root_uri, str(conf_dir))
        doctree_dir = build_dir / "doctrees"
        build_dir /= builder_name

        return {
            "buildername": builder_name,
            "confdir": str(conf_dir),
            "doctreedir": str(doctree_dir),
            "freshenv": self.force_full_build,
            "outdir": str(build_dir),
            "parallel": self.parallel,
            "srcdir": str(src_dir),
            "status": None,
            "warning": None,
        }

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

    hide_sphinx_output: bool = Field(False, alias="hideSphinxOutput")
    """A flag to indicate if Sphinx build output should be omitted from the log."""


class InitializationOptions(BaseModel):
    """The initialization options we can expect to receive from a client."""

    sphinx: SphinxConfig = Field(default_factory=SphinxConfig)
    """The ``esbonio.sphinx.*`` namespace of options."""

    server: SphinxServerConfig = Field(default_factory=SphinxServerConfig)
    """The ``esbonio.server.*`` namespace of options."""


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
            return (str(conf), None)

        path, *parts = location.split(":")
        lineno = None

        # On windows the rest of the path will be the first element of parts
        if IS_WIN:
            path += f":{parts.pop(0)}"

        if len(parts) == 1:
            try:
                lineno = int(parts[0])
            except ValueError:
                pass

        if len(parts) == 2:
            # TODO: There's a possibility that there is an error in a docstring in a
            #       *.py file somewhere. In which case parts would look like
            #       ['docstring of {dotted.name}', '{lineno}']
            #
            #  e.g. ['docstring of esbonio.lsp.sphinx.SphinxLanguageServer.get_domains', '8']
            #
            #       It would be good to handle this case and look up the correct line
            #       number to place a diagnostic.
            pass

        return (Uri.from_fs_path(path), lineno)

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
        self.translator.filter(record)

        loc = record.location if isinstance(record, SphinxLogRecord) else ""
        doc, lineno = self.get_location(loc)
        line = lineno or 1
        self.server.logger.debug("Reporting diagnostic at %s:%s", doc, line)

        try:
            message = record.msg % record.args
        except Exception:
            message = record.msg
            self.server.logger.debug(
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


class SphinxLanguageServer(RstLanguageServer):
    """A language server dedicated to working with Sphinx projects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app: Optional[Sphinx] = None
        """The Sphinx application instance."""

        self.preview_process: Optional[Process] = None
        """The process hosting the preview server."""

        self.preview_port: Optional[int] = None
        """The port the preview server is running on."""

        self._role_target_types: Optional[Dict[str, List[str]]] = None
        """Cache for role target types."""

    @property
    def configuration(self) -> Dict[str, Any]:
        """Return the server's actual configuration."""
        config = super().configuration

        if self.app:
            app = self.app
            builder_name = None if app.builder is None else app.builder.name
            config["sphinx"] = SphinxConfig(
                version=__sphinx_version__,
                confDir=app.confdir,
                srcDir=app.srcdir,
                buildDir=app.outdir,
                builderName=builder_name,
            )

        return config

    def initialize(self, params: InitializeParams):
        super().initialize(params)
        self.user_config = InitializationOptions(
            **typing.cast(Dict, params.initialization_options)
        )

    def initialized(self, params: InitializedParams):
        self.app = self._initialize_sphinx()
        self.build()

    def _initialize_sphinx(self):

        try:
            return self.create_sphinx_app(self.user_config)
        except MissingConfigError:
            self.show_message(
                message="Unable to find your 'conf.py', features that depend on Sphinx will be unavailable",
                msg_type=MessageType.Warning,
            )
            self.send_notification(
                "esbonio/buildComplete",
                {
                    "config": self.configuration,
                    "error": True,
                    "warnings": 0,
                },
            )
        except Exception as exc:
            self.logger.error(traceback.format_exc())
            uri, diagnostic = exception_to_diagnostic(exc)
            self.set_diagnostics("conf.py", uri, [diagnostic])

            self.sync_diagnostics()
            self.send_notification(
                "esbonio/buildComplete",
                {"config": self.configuration, "error": True, "warnings": 0},
            )

    def on_shutdown(self, *args):

        if self.preview_process:

            if not hasattr(self.preview_process, "kill"):
                self.preview_process.terminate()
            else:
                self.preview_process.kill()

    def save(self, params: DidSaveTextDocumentParams):
        super().save(params)

        filepath = Uri.to_fs_path(params.text_document.uri)
        if filepath.endswith("conf.py"):
            if self.app:
                conf_dir = pathlib.Path(self.app.confdir)
            else:
                # The user's config is currently broken... where should their conf.py be?
                if self.user_config is not None:
                    config = typing.cast(InitializationOptions, self.user_config).sphinx
                else:
                    config = SphinxConfig()

                conf_dir = config.resolve_conf_dir(
                    self.workspace.root_uri
                ) or pathlib.Path(".")

            if str(conf_dir / "conf.py") == filepath:
                self.clear_diagnostics("conf.py")
                self.sync_diagnostics()
                self.app = self._initialize_sphinx()

        else:
            self.clear_diagnostics("sphinx", params.text_document.uri)

        self.build()

    def delete_files(self, params: DeleteFilesParams):
        self.logger.debug("Deleted files: %s", params.files)

        # Files don't exist anymore, so diagnostics must be cleared.
        for file in params.files:
            self.clear_diagnostics("sphinx", file.uri)

        self.build()

    def build(self):

        if not self.app:
            return

        self.logger.debug("Building...")
        self.send_notification("esbonio/buildStart", {})
        self.clear_diagnostics("sphinx-build")
        self.sync_diagnostics()

        # Reset the warnings counter
        self.app._warncount = 0
        error = False
        self.sphinx_log.diagnostics = {}

        try:
            self.app.build()
        except Exception as exc:
            error = True
            self.logger.error(traceback.format_exc())
            uri, diagnostic = exception_to_diagnostic(exc)
            self.set_diagnostics("sphinx-build", uri, [diagnostic])

        for doc, diagnostics in self.sphinx_log.diagnostics.items():
            self.logger.debug("Found %d problems for %s", len(diagnostics), doc)
            self.set_diagnostics("sphinx", doc, diagnostics)

        self.sync_diagnostics()
        self.send_notification(
            "esbonio/buildComplete",
            {
                "config": self.configuration,
                "error": error,
                "warnings": self.app._warncount,
            },
        )

    def create_sphinx_app(self, options: InitializationOptions) -> Optional[Sphinx]:
        """Create a Sphinx application instance with the given config."""
        sphinx = options.sphinx
        server = options.server

        self.logger.debug("Workspace root '%s'", self.workspace.root_uri)
        self.logger.debug("User Config %s", json.dumps(sphinx.dict(), indent=2))

        sphinx_args = sphinx.get_sphinx_args(self.workspace.root_uri)
        self.logger.debug("Sphinx Args %s", json.dumps(sphinx_args, indent=2))

        # Disable color escape codes in Sphinx's log messages
        console.nocolor()
        app = Sphinx(**sphinx_args)

        # This has to happen after app creation otherwise our logging handler
        # will get cleared by Sphinx's setup.
        if not server.hide_sphinx_output:
            sphinx_logger = logging.getLogger("sphinx")
            sphinx_logger.setLevel(logging.INFO)

            self.sphinx_log = SphinxLogHandler(app, self)
            self.sphinx_log.setLevel(logging.INFO)

            formatter = logging.Formatter("%(message)s")
            self.sphinx_log.setFormatter(formatter)
            sphinx_logger.addHandler(self.sphinx_log)

        self._load_sphinx_extensions(app)
        self._load_sphinx_config(app)

        return app

    def _load_sphinx_extensions(self, app: Sphinx):
        """Loop through each of Sphinx's extensions and see if any contain server
        functionality.
        """

        for name, ext in app.extensions.items():
            mod = ext.module

            if name in self._loaded_modules:
                self.logger.debug("Skipping previously loaded module '%s'", name)

            if not hasattr(ext, "esbonio_setup"):
                continue

            self.logger.debug("Loading sphinx module '%s'", name)
            try:
                mod.esbonio_setup(self)
                self._loaded_modules[name] = mod
            except Exception:
                self.logger.error(
                    "Unable to load sphinx module '%s'\n%s",
                    name,
                    traceback.format_exc(),
                )

    def _load_sphinx_config(self, app: Sphinx):
        """Try and load the config as an server extension."""

        name = "<sphinx-config>"
        if name in self._loaded_modules:
            self.logger.debug("Skipping previously loaded module '%s'", name)
            return

        fn = app.config._raw_config.get("esbonio_setup", None)
        if not fn or not callable(fn):
            return

        self.logger.debug("Loading sphinx module '%s'", name)
        try:
            fn(self)
            self._loaded_modules[name] = fn
        except Exception:
            self.logger.error(
                "Unable to load sphinx module '%s'\n%s",
                name,
                traceback.format_exc(),
            )

    def preview(self, options: Dict[str, Any]) -> Dict[str, Any]:

        if not self.app or not self.app.builder:
            return {}

        builder_name = self.app.builder.name
        if builder_name not in {"html"}:
            self.show_message(
                f"Previews are not currently supported for the '{builder_name}' builder."
            )

            return {}

        if not self.preview_process and IS_LINUX:
            self.logger.debug("Starting preview server.")
            server = make_preview_server(self.app.outdir)
            self.preview_port = server.server_port

            self.preview_process = Process(target=server.serve_forever, daemon=True)
            self.preview_process.start()

        if not self.preview_process and not IS_LINUX:
            self.logger.debug("Starting preview server")

            q: Queue = Queue()
            self.preview_process = Process(
                target=start_preview_server, args=(q, self.app.outdir), daemon=True
            )
            self.preview_process.start()
            self.preview_port = q.get()

        if options.get("show", True):
            self.show_document(
                ShowDocumentParams(
                    uri=f"http://localhost:{self.preview_port}", external=True
                )
            )

        return {"port": self.preview_port}

    def get_doctree(
        self, *, docname: Optional[str] = None, uri: Optional[str] = None
    ) -> Optional[Any]:
        """Return the doctree that corresponds with the specified document.

        The ``docname`` of a document is its path relative to the project's ``srcdir``
        minus the extension e.g. the docname of the file ``docs/lsp/features.rst``
        would be ``lsp/features``.

        Parameters
        ----------
        docname:
           Returns the doctree that corresponds with the given docname
        uri:
           Returns the doctree that corresponds with the given uri.
        """

        if self.app is None or self.app.env is None or self.app.builder is None:
            return None

        if uri is not None:
            fspath = Uri.to_fs_path(uri)
            docname = self.app.env.path2doc(fspath)

        if docname is None:
            return None

        try:
            return self.app.env.get_and_resolve_doctree(docname, self.app.builder)
        except FileNotFoundError:
            self.logger.debug("Could not find doctree for '%s'", docname)
            # self.logger.debug(traceback.format_exc())
            return None

    def get_domain(self, name: str) -> Optional[Domain]:
        """Return the domain with the given name.

        If a domain with the given name cannot be found, this method will return None.

        Parameters
        ----------
        name:
           The name of the domain
        """

        if self.app is None or self.app.env is None:
            return None

        domains = self.app.env.domains
        return domains.get(name, None)

    def get_domains(self) -> Iterator[Tuple[str, Domain]]:
        """Get all the domains registered with an applications.

        Returns a generator that iterates through all of an application's domains,
        taking into account configuration variables such as ``primary_domain``.
        Yielded values will be a tuple of the form ``(prefix, domain)`` where

        - ``prefix`` is the namespace that should be used when referencing items
          in the domain
        - ``domain`` is the domain object itself.

        """

        if self.app is None or self.app.env is None:
            return []

        domains = self.app.env.domains
        primary_domain = self.app.config.primary_domain

        for name, domain in domains.items():
            prefix = name

            # Items from the standard and primary domains don't require the namespace prefix
            if name == "std" or name == primary_domain:
                prefix = ""

            yield prefix, domain

    def get_directives(self) -> Dict[str, Directive]:
        """Return a dictionary of the known directives"""

        if self._directives is not None:
            return self._directives

        self._directives = super().get_directives()

        for prefix, domain in self.get_domains():
            fmt = "{prefix}:{name}" if prefix else "{name}"

            for name, directive in domain.directives.items():
                key = fmt.format(name=name, prefix=prefix)
                self._directives[key] = directive

        return self._directives

    def get_directive_options(self, name: str) -> Dict[str, Any]:
        """Return the options specification for the given directive."""

        directive = self.get_directives().get(name, None)
        if directive is None:
            return {}

        options = directive.option_spec

        if name.startswith("auto") and self.app:
            self.logger.debug("Processing options for '%s' directive", name)
            name = name.replace("auto", "")

            self.logger.debug("Documenter name is '%s'", name)
            documenter = self.app.registry.documenters.get(name, None)

            if documenter is not None:
                options = documenter.option_spec

        return options or {}

    def get_roles(self) -> Dict[str, Any]:
        """Return a dictionary of known roles."""

        if self._roles is not None:
            return self._roles

        self._roles = super().get_roles()

        for prefix, domain in self.get_domains():
            fmt = "{prefix}:{name}" if prefix else "{name}"

            for name, role in domain.roles.items():
                key = fmt.format(name=name, prefix=prefix)
                self._roles[key] = role

        return self._roles

    def get_default_role(self) -> Tuple[Optional[str], Optional[str]]:
        """Return the project's default role"""

        if not self.app:
            return None, None

        role = self.app.config.default_role
        if not role:
            return None, None

        if ":" in role:
            domain, name = role.split(":")

            if domain == self.app.config.primary_domain:
                domain = ""

            return domain, name

        return None, role

    def get_role_target_types(self, name: str, domain_name: str = "") -> List[str]:
        """Return a map indicating which object types a role is capable of linking
        with.

        For example

        .. code-block:: python

           {
               "func": ["function"],
               "class": ["class", "exception"]
           }
        """

        key = f"{domain_name}:{name}" if domain_name else name

        if self._role_target_types is not None:
            return self._role_target_types.get(key, [])

        self._role_target_types = {}

        for prefix, domain in self.get_domains():
            fmt = "{prefix}:{name}" if prefix else "{name}"

            for name, item_type in domain.object_types.items():
                for role in item_type.roles:
                    role_key = fmt.format(name=role, prefix=prefix)
                    target_types = self._role_target_types.get(role_key, list())
                    target_types.append(name)

                    self._role_target_types[role_key] = target_types

        types = self._role_target_types.get(key, [])
        self.logger.debug("Role '%s' targets object types '%s'", key, types)

        return types

    def get_role_targets(self, name: str, domain: str = "") -> List[tuple]:
        """Return a list of objects targeted by the given role.

        Parameters
        ----------
        name:
           The name of the role
        domain:
           The domain the role is a part of, if applicable.
        """

        targets: List[tuple] = []
        domain_obj: Optional[Domain] = None

        if domain:
            domain_obj = self.get_domain(domain)
        else:
            std = self.get_domain("std")
            if std and name in std.roles:
                domain_obj = std

            elif self.app and self.app.config.primary_domain:
                domain_obj = self.get_domain(self.app.config.primary_domain)

        target_types = set(self.get_role_target_types(name, domain))

        if not domain_obj:
            self.logger.debug("Unable to find domain for role '%s:%s'", domain, name)
            return []

        for obj in domain_obj.get_objects():
            if obj[2] in target_types:
                targets.append(obj)

        return targets

    def get_intersphinx_projects(self) -> List[str]:
        """Return the list of configured intersphinx project names."""

        if self.app is None:
            return []

        inv = getattr(self.app.env, "intersphinx_named_inventory", {})
        return list(inv.keys())

    def has_intersphinx_targets(
        self, project: str, name: str, domain: str = ""
    ) -> bool:
        """Return ``True`` if the given intersphinx project has targets targeted by the
        given role.

        Parameters
        ----------
        project:
           The project to check
        name:
           The name of the role
        domain:
           The domain the role is a part of, if applicable.
        """

        targets = self.get_intersphinx_targets(project, name, domain)

        if len(targets) == 0:
            return False

        return any([len(items) > 0 for items in targets.values()])

    def get_intersphinx_targets(
        self, project: str, name: str, domain: str = ""
    ) -> Dict[str, Dict[str, tuple]]:
        """Return the intersphinx objects targeted by the given role.

        Parameters
        ----------
        project:
           The project to return targets from
        name:
           The name of the role
        domain:
           The domain the role is a part of, if applicable.
        """

        if self.app is None:
            return {}

        inv = getattr(self.app.env, "intersphinx_named_inventory", {})
        if project not in inv:
            return {}

        targets = {}
        inv = inv[project]

        for target_type in self.get_role_target_types(name, domain):

            explicit_domain = f"{domain}:{target_type}"
            if explicit_domain in inv:
                targets[target_type] = inv[explicit_domain]
                continue

            primary_domain = f'{self.app.config.primary_domain or ""}:{target_type}'
            if primary_domain in inv:
                targets[target_type] = inv[primary_domain]
                continue

            std_domain = f"std:{target_type}"
            if std_domain in inv:
                targets[target_type] = inv[std_domain]

        return targets


def exception_to_diagnostic(exc: BaseException):
    """Convert an exception into a diagnostic we can send to the client."""

    # Config errors sometimes wrap the true cause of the problem
    if isinstance(exc, ConfigError) and exc.__cause__ is not None:
        exc = exc.__cause__

    if isinstance(exc, SyntaxError):
        path = pathlib.Path(exc.filename or "")
        line = (exc.lineno or 1) - 1
    else:
        tb = exc.__traceback__
        frame = traceback.extract_tb(tb)[-1]
        path = pathlib.Path(frame.filename)
        line = frame.lineno - 1

    message = type(exc).__name__ if exc.args.count == 0 else exc.args[0]

    diagnostic = Diagnostic(
        range=Range(
            start=Position(line=line, character=0),
            end=Position(line=line + 1, character=0),
        ),
        message=message,
        severity=DiagnosticSeverity.Error,
    )

    return Uri.from_fs_path(str(path)), diagnostic


cli = setup_cli("esbonio.lsp.sphinx", "Esbonio's Sphinx language server.")
cli.set_defaults(modules=DEFAULT_MODULES)
cli.set_defaults(server_cls=SphinxLanguageServer)
