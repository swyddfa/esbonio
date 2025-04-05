from __future__ import annotations

import typing

from esbonio.sphinx_agent.types import Uri

from ._configuration import ConfigChangeEvent
from ._configuration import ConfigurationContext
from .events import EventSource
from .feature import CompletionConfig
from .feature import CompletionContext
from .feature import CompletionTrigger
from .feature import DefinitionContext
from .feature import DefinitionTrigger
from .feature import DocumentLinkContext
from .feature import HoverContext
from .feature import HoverTrigger
from .feature import LanguageFeature
from .server import EsbonioLanguageServer
from .server import EsbonioWorkspace
from .server import __version__
from .setup import create_language_server

if typing.TYPE_CHECKING:
    from .feature import UriContext  # noqa: F401

__all__ = (
    "__version__",
    "ConfigChangeEvent",
    "ConfigurationContext",
    "CompletionConfig",
    "CompletionContext",
    "CompletionTrigger",
    "DefinitionContext",
    "DefinitionTrigger",
    "DocumentLinkContext",
    "EsbonioLanguageServer",
    "EsbonioWorkspace",
    "EventSource",
    "HoverContext",
    "HoverTrigger",
    "LanguageFeature",
    "Uri",
    "create_language_server",
)
