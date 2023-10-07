"""Type definitions for the sphinx agent.

This is the *only* file shared between the agent itself and the parent language server.
For this reason this file *cannot* import anything from Sphinx.
"""
import dataclasses
import enum
from typing import Dict
from typing import List
from typing import Union


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

    build_file_map: Dict[str, str] = dataclasses.field(default_factory=dict)
    """A mapping of source files to the output files they contributed to."""


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
