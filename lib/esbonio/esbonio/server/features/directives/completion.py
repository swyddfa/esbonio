"""Helper functions for completion support"""

from __future__ import annotations

import re
import typing

from lsprotocol import types

from esbonio import server

if typing.TYPE_CHECKING:
    from typing import Callable
    from typing import Dict
    from typing import Optional
    from typing import Tuple

    from . import Directive

    DirectiveRenderer = Callable[
        [server.CompletionContext, Directive], Optional[types.CompletionItem]
    ]


WORD = re.compile("[a-zA-Z]+")
_DIRECTIVE_RENDERERS: Dict[Tuple[str, str], DirectiveRenderer] = {}
"""CompletionItem rendering functions for directives."""


def renderer(*, language: str, insert_behavior: str):
    """Define a new rendering function."""

    def fn(f: DirectiveRenderer) -> DirectiveRenderer:
        _DIRECTIVE_RENDERERS[(language, insert_behavior)] = f
        return f

    return fn


def get_directive_renderer(
    language: str, insert_behavior: str
) -> Optional[DirectiveRenderer]:
    """Return the directive renderer to use.

    Parameters
    ----------
    language
       The source language the completion item will be inserted into

    insert_behavior
       How the completion should behave when inserted.

    Returns
    -------
    Optional[DirectiveRenderer]
       The rendering function to use that matches the given criteria, if available.
    """
    return _DIRECTIVE_RENDERERS.get((language, insert_behavior), None)


@renderer(language="rst", insert_behavior="insert")
def render_rst_directive_with_insert_text(
    context: server.CompletionContext,
    directive: Directive,
) -> Optional[types.CompletionItem]:
    """Render a ``CompletionItem`` using ``insertText`` fields.

    This implements the ``insert`` behavior for directives.
    Parameters
    ----------
    context
       The context in which the completion is being generated.

    directive
       The directive.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item, or ``None`` if the directive should be skipped
    """
    insert_text = f".. {directive.name}::"
    user_text = context.match.group(0).strip()

    # Since we can't replace any existing text, it only makes sense
    # to offer completions that align with what the user has already written.
    if not insert_text.startswith(user_text):
        return None

    # Except that's not entirely true... to quote the LSP spec. (emphasis added)
    #
    # > in the model the client should filter against what the user has already typed
    # > **using the word boundary rules of the language** (e.g. resolving the word
    # > under the cursor position). The reason for this mode is that it makes it
    # > extremely easy for a server to implement a basic completion list and get it
    # > filtered on the client.
    #
    # So in other words... if the cursor is inside a word, that entire word will be
    # replaced with what we have in `insert_text` so we need to be able to do something
    # like
    #    ..         -> image::
    #    .. im      -> image::
    #
    #    ..         -> code-block::
    #    .. cod     -> code-block::
    #    .. code-bl -> block::
    #
    #    ..         -> c:function::
    #    .. c       -> c:function::
    #    .. c:      -> function::
    #    .. c:fun   -> function::
    #
    # And since the client is free to interpret this how it likes, it's unlikely we'll
    # be able to get this right in all cases for all clients. So for now this is going
    # to target Kate's interpretation since it currently does not support ``text_edit``
    # and it was the editor that prompted this to be implemented in the first place.
    #
    # See: https://github.com/swyddfa/esbonio/issues/471

    # If the existing text ends with a delimiter, then we should simply remove the
    # entire prefix
    if user_text.endswith((":", "-", " ")):
        start_index = len(user_text)

    # Look for groups of word chars, replace text until the start of the final group
    else:
        start_indices = [m.start() for m in WORD.finditer(user_text)] or [
            len(user_text)
        ]
        start_index = max(start_indices)

    item = _render_directive_common(directive)
    item.insert_text = insert_text[start_index:]
    item.insert_text_format = types.InsertTextFormat.PlainText
    return item


@renderer(language="rst", insert_behavior="replace")
def render_rst_directive_with_text_edit(
    context: server.CompletionContext,
    directive: Directive,
) -> Optional[types.CompletionItem]:
    """Render a ``CompletionItem`` for a reStructuredText directive using the
    ``textEdit`` field.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    directive
       The directive to render.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item, or ``None`` if the directive should be skipped
    """
    match = context.match

    # Calculate the range of text the CompletionItems should edit, we don't need to
    # touch indentation.
    start = match.span()[0] + match.group(0).find(".")

    if match.group("argument"):
        # If there is an existing argument to the directive, we should leave it
        # untouched
        end = match.span()[0] + match.group(0).find("::") + 2
    else:
        end = match.span()[1]

    insert_text = f".. {directive.name}::"

    item = _render_directive_common(directive)
    item.filter_text = insert_text
    item.insert_text_format = types.InsertTextFormat.PlainText
    item.text_edit = types.TextEdit(
        new_text=insert_text,
        range=types.Range(
            start=types.Position(line=context.position.line, character=start),
            end=types.Position(line=context.position.line, character=end),
        ),
    )

    return item


@renderer(language="markdown", insert_behavior="replace")
def render_myst_directive_with_text_edit(
    context: server.CompletionContext,
    directive: Directive,
) -> Optional[types.CompletionItem]:
    """Render a ``CompletionItem`` for a MyST directive using the ``textEdit`` field.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    directive
       The directive to render.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item
    """

    # Calculate the range of text the CompletionItems should edit, we don't need to
    # touch indentation.
    start = context.match.span()[0] + context.match.group(0).find("`")

    if has_argument := context.match.group("argument"):
        end = context.match.span()[0] + context.match.group(0).find("}") + 1
    else:
        end = context.match.span()[1]

    if context.snippet_support and not has_argument:
        insert_text = f"```{{{directive.name}}} $0\n```"
        insert_text_format = types.InsertTextFormat.Snippet
    else:
        insert_text = f"```{{{directive.name}}}"
        insert_text_format = types.InsertTextFormat.PlainText

    item = _render_directive_common(directive)
    item.filter_text = insert_text
    item.insert_text_format = insert_text_format
    item.text_edit = types.TextEdit(
        new_text=insert_text,
        range=types.Range(
            start=types.Position(line=context.position.line, character=start),
            end=types.Position(line=context.position.line, character=end),
        ),
    )

    return item


@renderer(language="markdown", insert_behavior="insert")
def render_myst_directive_with_insert_text(
    context: server.CompletionContext,
    directive: Directive,
) -> Optional[types.CompletionItem]:
    """Render a ``CompletionItem`` for a MyST directive using the ``insertText`` field.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    directive
       The directive to render.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item
    """
    if context.snippet_support:
        insert_text = f"```{{{directive.name}}} $0\n```"
        insert_text_format = types.InsertTextFormat.Snippet
    else:
        insert_text = f"```{{{directive.name}}}"
        insert_text_format = types.InsertTextFormat.PlainText

    user_text = context.match.group(0).strip()

    # Since we can't replace any existing text, it only makes sense
    # to offer completions that align with what the user has already written.
    if not insert_text.startswith(user_text):
        return None

    # See comment in `render_rst_directive_with_insert_text` above for an extended
    # discussion on how `insertText` completions work.

    # If the existing text ends with a delimiter, then we should simply remove the
    # entire prefix
    if user_text.endswith((":", "-", "{", "}", "`")):
        start_index = len(user_text)

    else:
        # Look for groups of word chars, replace text until the start of the final group
        start_indices = [m.start() for m in WORD.finditer(user_text)] or [
            len(user_text)
        ]
        start_index = max(start_indices)

    item = _render_directive_common(directive)
    item.insert_text = insert_text[start_index:]
    item.insert_text_format = insert_text_format

    return item


def _render_directive_common(directive: Directive) -> types.CompletionItem:
    """Render the common fields of a directive's completion item."""

    return types.CompletionItem(
        label=directive.name,
        detail=directive.implementation,
        kind=types.CompletionItemKind.Class,
        data={"completion_type": "directive"},
    )


# def _render_directive_option_with_insert_text(
#     context: CompletionContext,
#     directive: Directive,
# ) -> Optional[types.CompletionItem]:
#     """Render a directive option's ``CompletionItem`` using the ``insertText`` field.

#     This implements the ``insert`` insert behavior for directive options.

#     Parameters
#     ----------
#     context
#        The context in which the completion is being generated.

#     name
#        The name of the directive option, as it appears in an rst file.

#     directive
#        The name of the directive, as it appears in an rst file.

#     implementation
#        The class implementing the directive.

#     """

#     insert_text = f":{name}:"
#     user_text = context.match.group(0).strip()

#     if not insert_text.startswith(user_text):
#         return None

#     if user_text.endswith((":", "-", " ")):
#         start_index = len(user_text)

#     else:
#         start_indices = [m.start() for m in WORD.finditer(user_text)] or [
#             len(user_text)
#         ]
#         start_index = max(start_indices)

#     item = _render_directive_option_common(name, directive, implementation)
#     item.insert_text = insert_text[start_index:]
#     return item


# def _render_directive_option_with_text_edit(
#     context: CompletionContext,
#     name: str,
#     directive: str,
#     implementation: Type[Directive],
# ) -> CompletionItem:
#     """Render a directive option's ``CompletionItem`` using the``textEdit`` field.

#     This implements the ``replace`` insert behavior for directive options.

#     Parameters
#     ----------
#     context
#        The context in which the completion is being generated.

#     name
#        The name of the directive option, as it appears in an rst file.

#     directive
#        The name of the directive, as it appears in an rst file.

#     implementation
#        The class implementing the directive.

#     """

#     match = context.match
#     groups = match.groupdict()

#     option = groups["option"]
#     start = match.span()[0] + match.group(0).find(option)
#     end = start + len(option)

#     range_ = Range(
#         start=Position(line=context.position.line, character=start),
#         end=Position(line=context.position.line, character=end),
#     )

#     insert_text = f":{name}:"

#     item = _render_directive_option_common(name, directive, implementation)
#     item.filter_text = insert_text
#     item.text_edit = TextEdit(range=range_, new_text=insert_text)

#     return item


# def _render_directive_option_common(
#     name: str, directive: str, impl: Type[Directive]
# ) -> CompletionItem:
#     """Render the common fields of a directive option's completion item."""

#     try:
#         impl_name = f"{impl.__module__}.{impl.__name__}"
#     except AttributeError:
#         impl_name = f"{impl.__module__}.{impl.__class__.__name__}"

#     return CompletionItem(
#         label=name,
#         detail=f"{impl_name}:{name}",
#         kind=CompletionItemKind.Field,
#         data={"completion_type": "directive_option", "for_directive": directive},
#     )
