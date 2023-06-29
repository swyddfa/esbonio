"""Type definitions for the sphinx agent.

This is the *only* file shared between the agent itself and the parent language server.
For this reason this file *cannot* import anything from Sphinx.
"""
import dataclasses
from typing import List
from typing import Union


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

    version: str

    conf_dir: str

    build_dir: str

    builder_name: str

    src_dir: str


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


@dataclasses.dataclass
class BuildResult:
    """Results from a ``sphinx/build`` request."""

    placeholder: str = "TODO: Real results"


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


METHOD_TO_MESSAGE_TYPE = {"sphinx/createApp": CreateApplicationRequest}
METHOD_TO_RESPONSE_TYPE = {"sphinx/createApp": CreateApplicationResponse}
