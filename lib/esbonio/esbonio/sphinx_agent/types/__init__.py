"""Type definitions for the sphinx agent.

This is the *only* file shared between the agent itself and the parent language server.
For this reason this file *cannot* import anything from Sphinx.
"""

import dataclasses
import os
import pathlib
import re
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from urllib import parse

from .lsp import Diagnostic
from .lsp import DiagnosticSeverity
from .lsp import Location
from .lsp import Position
from .lsp import Range
from .roles import MYST_ROLE
from .roles import RST_DEFAULT_ROLE
from .roles import RST_ROLE
from .roles import Role

__all__ = (
    "Diagnostic",
    "DiagnosticSeverity",
    "Location",
    "MYST_ROLE",
    "Position",
    "RST_DEFAULT_ROLE",
    "RST_ROLE",
    "Range",
    "Role",
)

MYST_DIRECTIVE: "re.Pattern" = re.compile(
    r"""
    (\s*)                             # directives can be indented
    (?P<directive>
      ```(`*)?                        # directives start with at least 3 ` chars
      (?!\w)                          # -- regular code blocks are not directives
      [{]?                            # followed by an opening brace
      (?P<name>[^}]+)?                # directives have a name
      [}]?                            # directives are closed with a closing brace
    )
    (\s+(?P<argument>.*?)\s*$)?       # directives may take an argument
    """,
    re.VERBOSE,
)
"""A regular expression to detect and parse partial and complete MyST directives.

This does **not** include any options or content that may be included with the
initial declaration.
"""


RST_DIRECTIVE: "re.Pattern" = re.compile(
    r"""
    (\s*)                             # directives can be indented
    (?P<directive>
      \.\.                            # directives start with a comment
      [ ]?                            # followed by a space
      (?P<substitution>\|             # this could be a substitution definition
        (?P<substitution_text>[^|]+)?
      \|?)?
      [ ]?
      (?P<name>([\w-]|:(?!:))+)?      # directives have a name
      (::)?                           # directives end with '::'
    )
    ([\s]+(?P<argument>.*?)\s*$)?     # directives may take an argument
    """,
    re.VERBOSE,
)
"""A regular expression to detect and parse partial and complete directives.

This does **not** include any options or content that may be included underneath
the initial declaration. A number of named capture groups are available.

``name``
   The name of the directive, not including the domain prefix.

``directive``
   Everything that makes up a directive, from the initial ``..`` up to and including the
   ``::`` characters.

``argument``
   All argument text.

``substitution``
   If the directive is part of a substitution definition, this group will contain
"""


RST_DIRECTIVE_OPTION: "re.Pattern" = re.compile(
    r"""
    (?P<indent>\s+)       # directive options must be indented
    (?P<option>
      :                   # options start with a ':'
      (?P<name>[\w-]+)?   # options have a name
      :?                  # options end with a ':'
    )
    (\s*
      (?P<value>.*)       # options can have a value
    )?
    """,
    re.VERBOSE,
)
"""A regular expression used to detect and parse partial and complete directive options.

A number of named capture groups are available

``name``
   The name of the option

``option``
   The name of the option including the surrounding ``:`` characters.

``indent``
   The whitespace characters making preceeding the initial ``:`` character

``value``
   The value passed to the option

"""


IS_WIN = os.name == "nt"
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z\d+.-]*$")
RE_DRIVE_LETTER_PATH = re.compile(r"^(\/?)([a-zA-Z]:)")


# TODO: Look into upstreaming this into pygls
#       - if it works out
#       - when pygls drops 3.7 (Uri uses the := operator)
@dataclasses.dataclass(frozen=True)
class Uri:
    """Helper class for working with URIs."""

    scheme: str

    authority: str

    path: str

    query: str

    fragment: str

    def __post_init__(self):
        """Basic validation."""
        if self.scheme is None:
            raise ValueError("URIs must have a scheme")

        if not SCHEME.match(self.scheme):
            raise ValueError("Invalid scheme")

        if self.authority and self.path and (not self.path.startswith("/")):
            raise ValueError("Paths with an authority must start with a slash '/'")

        if self.path and self.path.startswith("//") and (not self.authority):
            raise ValueError(
                "Paths without an authority cannot start with two slashes '//'"
            )

    def __eq__(self, other):
        if type(other) is not type(self):
            return False

        if self.scheme != other.scheme:
            return False

        if self.authority != other.authority:
            return False

        if self.query != other.query:
            return False

        if self.fragment != other.fragment:
            return False

        if IS_WIN and self.scheme == "file":
            # Filepaths on windows are case in-sensitive
            if self.path.lower() != other.path.lower():
                return False

        elif self.path != other.path:
            return False

        return True

    def __hash__(self):
        if IS_WIN and self.scheme == "file":
            # Filepaths on windows are case in-sensitive
            path = self.path.lower()
        else:
            path = self.path

        return hash((self.scheme, self.authority, path, self.query, self.fragment))

    def __fspath__(self):
        """Return the file system representation of this uri.

        This makes Uri instances compatible with any function that expects an
        ``os.PathLike`` object!
        """
        # TODO: Should we raise an exception if scheme != "file"?
        return self.as_fs_path(preserve_case=True)

    def __str__(self):
        return self.as_string()

    def __truediv__(self, other):
        return self.join(other)

    @classmethod
    def create(
        cls,
        *,
        scheme: str = "",
        authority: str = "",
        path: str = "",
        query: str = "",
        fragment: str = "",
    ) -> "Uri":
        """Create a uri with the given attributes."""

        if scheme in {"http", "https", "file"}:
            if not path.startswith("/"):
                path = f"/{path}"

        return cls(
            scheme=scheme,
            authority=authority,
            path=path,
            query=query,
            fragment=fragment,
        )

    @classmethod
    def parse(cls, uri: str) -> "Uri":
        """Parse the given uri from its string representation."""
        scheme, authority, path, _, query, fragment = parse.urlparse(uri)
        return cls.create(
            scheme=parse.unquote(scheme),
            authority=parse.unquote(authority),
            path=parse.unquote(path),
            query=parse.unquote(query),
            fragment=parse.unquote(fragment),
        )

    def resolve(self) -> "Uri":
        """Return the fully resolved version of this Uri."""

        # This operation only makes sense for file uris
        if self.scheme != "file":
            return Uri.parse(str(self))

        return Uri.for_file(pathlib.Path(self).resolve())

    @classmethod
    def for_file(cls, filepath: Union[str, "os.PathLike[str]"]) -> "Uri":
        """Create a uri based on the given filepath."""

        fpath = os.fspath(filepath)
        if IS_WIN:
            fpath = fpath.replace("\\", "/")

        if fpath.startswith("//"):
            authority, *path = fpath[2:].split("/")
            fpath = "/".join(path)
        else:
            authority = ""

        return cls.create(scheme="file", authority=authority, path=fpath)

    @property
    def fs_path(self) -> Optional[str]:
        """Return the equivalent fs path."""
        return self.as_fs_path()

    def where(self, **kwargs) -> "Uri":
        """Return an transformed version of this uri where certain components of the uri
        have been replace with the given arguments.

        Passing a value of ``None`` will remove the given component entirely.
        """
        keys = {"scheme", "authority", "path", "query", "fragment"}
        valid_keys = keys.copy() & kwargs.keys()

        current = {k: getattr(self, k) for k in keys}
        replacements = {k: kwargs[k] for k in valid_keys}

        return Uri.create(**{**current, **replacements})

    def join(self, path: str) -> "Uri":
        """Join this Uri's path component with the given path and return the resulting
        uri.

        Parameters
        ----------
        path
           The path segment to join

        Returns
        -------
        Uri
           The resulting uri
        """

        if not self.path:
            raise ValueError("This uri has no path")

        if IS_WIN:
            fs_path = self.fs_path
            if fs_path is None:
                raise ValueError("Unable to join paths, fs_path is None")

            joined = os.path.normpath(os.path.join(fs_path, path))
            new_path = self.for_file(joined).path
        else:
            new_path = os.path.normpath(os.path.join(self.path, path))

        return self.where(path=new_path)

    def as_fs_path(self, preserve_case: bool = False) -> Optional[str]:
        """Return the file system path correspondin with this uri."""
        if self.path:
            path = _normalize_path(self.path, preserve_case)

            if self.authority and len(path) > 1:
                path = f"//{self.authority}{path}"

            # Remove the leading `/` from windows paths
            elif RE_DRIVE_LETTER_PATH.match(path):
                path = path[1:]

            if IS_WIN:
                path = path.replace("/", "\\")

            return path

        return None

    def as_string(self, encode=True) -> str:
        """Return a string representation of this Uri.

        Parameters
        ----------
        encode
           If ``True`` (the default), encode any special characters.

        Returns
        -------
        str
           The string representation of the Uri
        """

        # See: https://github.com/python/mypy/issues/10740
        encoder: Callable[[str], str] = parse.quote if encode else _replace_chars  # type: ignore[assignment]

        if authority := self.authority:
            usercred, *auth = authority.split("@")
            if len(auth) > 0:
                *user, cred = usercred.split(":")
                if len(user) > 0:
                    usercred = encoder(":".join(user)) + f":{encoder(cred)}"
                else:
                    usercred = encoder(usercred)
                authority = "@".join(auth)
            else:
                usercred = ""

            authority = authority.lower()
            *auth, port = authority.split(":")
            if len(auth) > 0:
                authority = encoder(":".join(auth)) + f":{port}"
            else:
                authority = encoder(authority)

            if usercred:
                authority = f"{usercred}@{authority}"

        scheme_separator = ""
        if authority or self.scheme == "file":
            scheme_separator = "//"

        if path := self.path:
            path = encoder(_normalize_path(path))

        if query := self.query:
            query = encoder(query)

        if fragment := self.fragment:
            fragment = encoder(fragment)

        parts = [
            f"{self.scheme}:",
            scheme_separator,
            authority if authority else "",
            path if path else "",
            f"?{query}" if query else "",
            f"#{fragment}" if fragment else "",
        ]
        return "".join(parts)


def _replace_chars(segment: str) -> str:
    """Replace a certain subset of characters in a uri segment"""
    return segment.replace("#", "%23").replace("?", "%3F")


def _normalize_path(path: str, preserve_case: bool = False) -> str:
    """Normalise the path segment of a Uri.

    Parameters
    ----------
    path
       The path to normalise.

    preserve_case
       If ``True``, preserve the case of the drive label on Windows.
       If ``False``, the drive label will be lowercased.

    Returns
    -------
    str
       The normalised path.
    """

    # normalize to fwd-slashes on windows,
    # on other systems bwd-slashes are valid
    # filename character, eg /f\oo/ba\r.txt
    if IS_WIN:
        path = path.replace("\\", "/")

    # Normalize drive paths to lower case
    if (not preserve_case) and (match := RE_DRIVE_LETTER_PATH.match(path)):
        path = match.group(1) + match.group(2).lower() + path[match.end() :]

    return path


# -- DB Types
#
# These represent the structure of data as stored in the SQLite database
Directive = Tuple[str, Optional[str], Optional[str]]
Symbol = Tuple[  # Represents either a document symbol or workspace symbol depending on context.
    int,  # id
    str,  # name
    int,  # kind
    str,  # detail
    str,  # range - as json object
    Optional[int],  # parent_id
    int,  # order_id
]


@dataclasses.dataclass
class CreateApplicationParams:
    """Parameters of a ``sphinx/createApp`` request."""

    command: List[str]
    """The ``sphinx-build`` command to base the app instance on."""


@dataclasses.dataclass
class CreateApplicationRequest:
    """A ``sphinx/createApp`` request."""

    id: Union[int, str]

    params: CreateApplicationParams

    method: str = "sphinx/createApp"

    jsonrpc: str = dataclasses.field(default="2.0")


@dataclasses.dataclass
class SphinxInfo:
    """Represents information about an instance of the Sphinx application."""

    version: str
    """The version of Sphinx being used."""

    conf_dir: str
    """The folder containing the project's conf.py"""

    build_dir: str
    """The folder containing the Sphinx application's build output"""

    builder_name: str
    """The name of the builder in use"""

    src_dir: str
    """The folder containing the source files for the project"""

    dbpath: str
    """The filepath the database is stored in."""


@dataclasses.dataclass
class CreateApplicationResponse:
    """A ``sphinx/createApp`` response."""

    id: Union[int, str]

    result: SphinxInfo

    jsonrpc: str = dataclasses.field(default="2.0")


@dataclasses.dataclass
class BuildParams:
    """Parameters of a ``sphinx/build`` request."""

    filenames: List[str] = dataclasses.field(default_factory=list)

    force_all: bool = False

    content_overrides: Dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class BuildResult:
    """Results from a ``sphinx/build`` request."""

    diagnostics: Dict[str, List[Diagnostic]] = dataclasses.field(default_factory=dict)
    """Any diagnostics associated with the project."""


@dataclasses.dataclass
class BuildRequest:
    """A ``sphinx/build`` request."""

    id: Union[int, str]

    params: BuildParams

    method: str = "sphinx/build"

    jsonrpc: str = dataclasses.field(default="2.0")


@dataclasses.dataclass
class BuildResponse:
    """A ``sphinx/build`` response."""

    id: Union[int, str]

    result: BuildResult

    jsonrpc: str = dataclasses.field(default="2.0")


@dataclasses.dataclass
class LogMessageParams:
    """Parameters of a ``window/logMessage`` notification."""

    type: int

    message: str


@dataclasses.dataclass
class LogMessage:
    """A ``window/logMessage`` notification"""

    params: LogMessageParams

    method: str = "window/logMessage"

    jsonrpc: str = dataclasses.field(default="2.0")


@dataclasses.dataclass
class ProgressParams:
    message: Optional[str] = None

    percentage: Optional[int] = None


@dataclasses.dataclass
class ProgressMessage:
    """A ``$/progress`` notification"""

    params: ProgressParams

    method: str = "$/progress"

    jsonrpc: str = dataclasses.field(default="2.0")


@dataclasses.dataclass
class ExitNotification:
    """An ``exit`` notification"""

    params: None

    method: str = "exit"

    jsonrpc: str = dataclasses.field(default="2.0")


METHOD_TO_MESSAGE_TYPE = {
    BuildRequest.method: BuildRequest,
    ExitNotification.method: ExitNotification,
    CreateApplicationRequest.method: CreateApplicationRequest,
}
METHOD_TO_RESPONSE_TYPE = {
    BuildRequest.method: BuildResponse,
    ExitNotification.method: None,
    CreateApplicationRequest.method: CreateApplicationResponse,
}
