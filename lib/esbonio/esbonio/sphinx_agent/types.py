import dataclasses
from typing import List
from typing import Union


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
