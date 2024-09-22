"""Type definitions for the sphinx agent.

This is the *only* module shared between the agent itself and the parent language
server. For this reason this module *cannot* import anything from Sphinx.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Any
from typing import Optional
from typing import Union

from .lsp import Diagnostic
from .lsp import DiagnosticSeverity
from .lsp import Location
from .lsp import Position
from .lsp import Range
from .roles import MYST_ROLE
from .roles import RST_DEFAULT_ROLE
from .roles import RST_ROLE
from .roles import Role
from .uri import IS_WIN
from .uri import Uri

__all__ = (
    "Diagnostic",
    "DiagnosticSeverity",
    "IS_WIN",
    "Location",
    "MYST_ROLE",
    "Position",
    "RST_DEFAULT_ROLE",
    "RST_ROLE",
    "Range",
    "Role",
    "Uri",
)

MYST_DIRECTIVE: re.Pattern = re.compile(
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


RST_DIRECTIVE: re.Pattern = re.compile(
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


RST_DIRECTIVE_OPTION: re.Pattern = re.compile(
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


# -- DB Types
#
# These represent the structure of data as stored in the SQLite database
Directive = tuple[str, Optional[str], Optional[str]]
Symbol = tuple[  # Represents either a document symbol or workspace symbol depending on context.
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

    command: list[str]
    """The ``sphinx-build`` command to base the app instance on."""

    config_overrides: dict[str, Any]
    """Overrides to apply to the application's configuration."""


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

    filenames: list[str] = dataclasses.field(default_factory=list)

    force_all: bool = False

    content_overrides: dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class BuildResult:
    """Results from a ``sphinx/build`` request."""

    diagnostics: dict[str, list[Diagnostic]] = dataclasses.field(default_factory=dict)
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
