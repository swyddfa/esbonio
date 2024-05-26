from __future__ import annotations

import typing
from dataclasses import dataclass
from dataclasses import field

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable
    from typing import Dict
    from typing import List
    from typing import Optional
    from typing import Tuple

    from .lsp import Location


@dataclass
class Role:
    """Represents a role."""

    @dataclass
    class TargetProvider:
        """A target provider instance."""

        name: str
        """The name of the provider."""

        kwargs: Dict[str, Any] = field(default_factory=dict)
        """Arguments to pass to the target provider."""

    name: str
    """The name of the role, as the user would type in an rst file."""

    implementation: Optional[str]
    """The dotted name of the role's implementation."""

    location: Optional[Location] = field(default=None)
    """The location of the role's implementation, if known."""

    target_providers: List[TargetProvider] = field(default_factory=list)
    """The list of target providers that can be used with this role."""

    def to_db(
        self, dumps: Callable[[Any], str]
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        """Convert this role to its database representation."""
        if len(self.target_providers) > 0:
            providers = dumps(self.target_providers)
        else:
            providers = None

        location = dumps(self.location) if self.location is not None else None
        return (self.name, self.implementation, location, providers)
