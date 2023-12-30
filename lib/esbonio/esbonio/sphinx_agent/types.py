"""Type definitions for the sphinx agent.

This is the *only* file shared between the agent itself and the parent language server.
For this reason this file *cannot* import anything from Sphinx.
"""
import dataclasses
import enum
import re
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

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
      ((?P<domain>[\w]+):(?!:))?      # directives may include a domain
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

``domain``
   The domain prefix

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


RST_ROLE = re.compile(
    r"""
    ([^\w:]|^\s*)                     # roles cannot be preceeded by letter chars
    (?P<role>
      :                               # roles begin with a ':' character
      (?!:)                           # the next character cannot be a ':'
      ((?P<domain>[\w]+):(?=\w))?     # roles may include a domain (that must be followed by a word character)
      ((?P<name>[\w-]+):?)?           # roles have a name
    )
    (?P<target>
      `                               # targets begin with a '`' character
      ((?P<alias>[^<`>]*?)<)?         # targets may specify an alias
      (?P<modifier>[!~])?             # targets may have a modifier
      (?P<label>[^<`>]*)?             # targets contain a label
      >?                              # labels end with a '>' when there's an alias
      `?                              # targets end with a '`' character
    )?
    """,
    re.VERBOSE,
)
"""A regular expression to detect and parse parial and complete roles.

I'm not sure if there are offical names for the components of a role, but the
language server breaks a role down into a number of parts::

                 vvvvvv label
                v modifier(optional)
               vvvvvvvv target
   :c:function:`!malloc`
   ^^^^^^^^^^^^ role
      ^^^^^^^^ name
    ^ domain (optional)

The language server sometimes refers to the above as a "plain" role, in that the
role's target contains just the label of the object it is linking to. However it's
also possible to define "aliased" roles, where the link text in the final document
is overriden, for example::

                vvvvvvvvvvvvvvvvvvvvvvvv alias
                                          vvvvvv label
                                         v modifier (optional)
               vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv target
   :c:function:`used to allocate memory <~malloc>`
   ^^^^^^^^^^^^ role
      ^^^^^^^^ name
    ^ domain (optional)

"""


RST_DEFAULT_ROLE = re.compile(
    r"""
    (?<![:`])
    (?P<target>
      `                               # targets begin with a '`' character
      ((?P<alias>[^<`>]*?)<)?         # targets may specify an alias
      (?P<modifier>[!~])?             # targets may have a modifier
      (?P<label>[^<`>]*)?             # targets contain a label
      >?                              # labels end with a '>' when there's an alias
      `?                              # targets end with a '`' character
    )
    """,
    re.VERBOSE,
)
"""A regular expression to detect and parse parial and complete "default" roles.

A "default" role is the target part of a normal role - but without the ``:name:`` part.
"""

# Could represent either a document symbol or workspace symbol depending on context.
Symbol = Tuple[
    int,  # id
    str,  # name
    int,  # kind
    str,  # detail
    str,  # range - as json object
    Optional[int],  # parent_id
    int,  # order_id
]


@dataclasses.dataclass(frozen=True)
class Position:
    line: int
    character: int


@dataclasses.dataclass(frozen=True)
class Range:
    start: Position
    end: Position


class DiagnosticSeverity(enum.IntEnum):
    Error = 1
    Warning = 2
    Information = 3
    Hint = 4


@dataclasses.dataclass(frozen=True)
class Diagnostic:
    range: Range
    message: str
    severity: DiagnosticSeverity


@dataclasses.dataclass
class CreateApplicationParams:
    """Parameters of a ``sphinx/createApp`` request."""

    command: List[str]
    """The ``sphinx-build`` command to base the app instance on."""

    enable_sync_scrolling: bool
    """Enable/disable sync scolling of previews."""


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

    id: str
    """A unique id representing a particular Sphinx application instance."""

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
