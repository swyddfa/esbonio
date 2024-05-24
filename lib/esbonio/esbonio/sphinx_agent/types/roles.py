from __future__ import annotations

import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from typing import Optional
    from typing import Tuple


@dataclass
class Role:
    """Represents a role."""

    name: str
    """The name of the role, as the user would type in an rst file."""

    implementation: Optional[str]
    """The dotted name of the role's implementation."""

    def to_db(self) -> Tuple[str, Optional[str], None]:
        """Convert this role to its database representation."""
        return (self.name, self.implementation, None)
