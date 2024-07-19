from __future__ import annotations

import re
import typing
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List

from .lsp import Location

if typing.TYPE_CHECKING:
    from typing import Callable
    from typing import Optional
    from typing import Tuple
    from typing import Type
    from typing import TypeVar

    T = TypeVar("T")
    JsonLoader = Callable[[str, Type[T]], T]


MYST_ROLE: re.Pattern = re.compile(
    r"""
    ([^\w`]|^\s*)                     # roles cannot be preceeded by letter chars
    (?P<role>
      {                               # roles start with a '{'
      (?P<name>[:\w+-]+)?             # roles have a name
      }?                              # roles end with a '}'
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
   {c:function}`!malloc`
   ^^^^^^^^^^^^ role
    ^^^^^^^^^^ name

The language server sometimes refers to the above as a "plain" role, in that the
role's target contains just the label of the object it is linking to. However it's
also possible to define "aliased" roles, where the link text in the final document
is overriden, for example::

                vvvvvvvvvvvvvvvvvvvvvvvv alias
                                          vvvvvv label
                                         v modifier (optional)
               vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv target
   {c:function}`used to allocate memory <~malloc>`
   ^^^^^^^^^^^^ role
    ^^^^^^^^^^ name

"""


RST_ROLE = re.compile(
    r"""
    ([^\w:]|^\s*)                     # roles cannot be preceeded by letter chars
    (?P<role>
      :                               # roles begin with a ':' character
      (?!:)                           # the next character cannot be a ':'
      ((?P<name>\w([:\w+-]*\w)?):?)?  # roles have a name
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
    ^^^^^^^^^^ name

The language server sometimes refers to the above as a "plain" role, in that the
role's target contains just the label of the object it is linking to. However it's
also possible to define "aliased" roles, where the link text in the final document
is overriden, for example::

                vvvvvvvvvvvvvvvvvvvvvvvv alias
                                          vvvvvv label
                                         v modifier (optional)
               vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv target
   :c:function:`used to allocate memory <~malloc>`
   ^^^^^^^^^^^^ role
    ^^^^^^^^^^ name

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

    @classmethod
    def from_db(
        cls,
        load_as: JsonLoader,
        name: str,
        implementation: Optional[str],
        location: Optional[str],
        providers: Optional[str],
    ) -> Role:
        """Convert this role to its database representation."""

        loc = load_as(location, Location) if location is not None else None
        target_providers = (
            load_as(providers, List[Role.TargetProvider])
            if providers is not None
            else []
        )

        return cls(
            name=name,
            implementation=implementation,
            location=loc,
            target_providers=target_providers,
        )
