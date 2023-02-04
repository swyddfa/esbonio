from typing import List

import attrs

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore[assignment]


@attrs.define
class ServerCompletionConfig:
    """Configuration options for the server that control completion behavior."""

    preferred_insert_behavior: Literal["insert", "replace"] = attrs.field(
        default="replace"
    )
    """This option indicates if the user prefers we use ``insertText`` or ``textEdit``
    when rendering ``CompletionItems``."""


@attrs.define
class ServerConfig:
    """Configuration options for the server."""

    completion: ServerCompletionConfig = attrs.field(factory=ServerCompletionConfig)
    """Configuration values that affect completion"""

    enable_scroll_sync: bool = attrs.field(default=False)
    """Enable custom transformation to add classes with line numbers"""

    enable_live_preview: bool = attrs.field(default=False)
    """Set it to True if you want to build Sphinx app on change event"""

    log_filter: List[str] = attrs.field(factory=list)
    """A list of logger names to restrict output to."""

    log_level: str = attrs.field(default="error")
    """The logging level of server messages to display."""

    show_deprecation_warnings: bool = attrs.field(default=False)
    """Developer flag to enable deprecation warnings."""


@attrs.define
class InitializationOptions:
    """The initialization options we can expect to receive from a client."""

    server: ServerConfig = attrs.field(factory=ServerConfig)
    """The ``esbonio.server.*`` namespace of options."""
