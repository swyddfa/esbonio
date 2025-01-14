from __future__ import annotations

import re
import typing
from dataclasses import dataclass
from dataclasses import field
from typing import Any

from .lsp import Location

if typing.TYPE_CHECKING:
    from typing import Callable
    from typing import TypeVar

    T = TypeVar("T")
    JsonLoader = Callable[[str, type[T]], T]


MYST_DIRECTIVE: re.Pattern = re.compile(
    r"""
    (\s*)                             # directives can be indented
    (?P<directive>
      ```(`*)?                        # directives start with at least 3 ` chars
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


@dataclass
class Directive:
    """Represents a directive."""

    @dataclass
    class ArgumentProvider:
        """An argument provider instance."""

        name: str
        """The name of the provider."""

        kwargs: dict[str, Any] = field(default_factory=dict)
        """Arguments to pass to the argument provider"""

    name: str
    """The name of the directive, as the user would type in an rst file."""

    implementation: str | None
    """The dotted name of the directive's implementation."""

    location: Location | None = field(default=None)
    """The location of the directive's implementation, if known"""

    argument_providers: list[ArgumentProvider] = field(default_factory=list)
    """The list of argument providers that can be used with this directive."""

    def to_db(
        self, dumps: Callable[[Any], str]
    ) -> tuple[str, str | None, str | None, str | None]:
        """Convert this directive to its database representation"""

        providers = None
        if len(self.argument_providers) > 0:
            providers = dumps(self.argument_providers)

        location = dumps(self.location) if self.location is not None else None
        return (self.name, self.implementation, location, providers)

    @classmethod
    def from_db(
        cls,
        load_as: JsonLoader,
        name: str,
        implementation: str | None,
        location: str | None,
        providers: str | None,
    ) -> Directive:
        """Create a directive from its database representation"""

        loc = load_as(location, Location) if location is not None else None
        argument_providers = (
            load_as(providers, list[Directive.ArgumentProvider])
            if providers is not None
            else []
        )

        return cls(
            name=name,
            implementation=implementation,
            location=loc,
            argument_providers=argument_providers,
        )
