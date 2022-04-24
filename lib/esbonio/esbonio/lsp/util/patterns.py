import re


DIRECTIVE = re.compile(
    r"""
    (\s*)                             # directives can be indented
    (?P<directive>
      \.\.                            # directives start with a comment
      [ ]?                            # followed by a space
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
the initial declaration. The language server breaks a directive down into a number
of parts::

                   vvvvvv argument
   .. c:function:: malloc
   ^^^^^^^^^^^^^^^ directive
        ^^^^^^^^ name
      ^ domain (optional)
"""


DIRECTIVE_OPTION = re.compile(
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

The language server breaks an option down into a number of parts::

               vvvvvv value
   |   :align: center
       ^^^^^^^ option
        ^^^^^ name
    ^^^ indent
"""
ROLE = re.compile(
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

See :func:`tests.test_roles.test_role_regex` for a list of example strings this pattern
is expected to match.
"""


DEFAULT_ROLE = re.compile(
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
