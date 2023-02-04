import re
from typing import Optional
from typing import Type

from docutils.parsers.rst import Directive
from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionItemKind
from lsprotocol.types import InsertTextFormat
from lsprotocol.types import Position
from lsprotocol.types import Range
from lsprotocol.types import TextEdit

from esbonio.lsp import CompletionContext

__all__ = ["render_directive_completion", "render_directive_option_completion"]


WORD = re.compile("[a-zA-Z]+")


def render_directive_completion(
    context: CompletionContext,
    name: str,
    directive: Type[Directive],
) -> Optional[CompletionItem]:
    """Render the given directive as a ``CompletionItem`` according to the current
    context.

    Parameters
    ----------
    context
       The context in which the completion should be rendered.

    name
       The name of the directive, as it appears in an rst file.

    directive
       The class that implements the directive.

    Returns
    -------
    Optional[CompletionItem]
       The final completion item or ``None``.
       If ``None`` is returned, then the given completion should be skipped.
    """

    if context.config.preferred_insert_behavior == "insert":
        return _render_directive_with_insert_text(context, name, directive)

    return _render_directive_with_text_edit(context, name, directive)


def render_directive_option_completion(
    context: CompletionContext,
    name: str,
    directive: str,
    implementation: Type[Directive],
) -> Optional[CompletionItem]:
    """Render the given directive option as a ``CompletionItem`` according to the
    current context.

    Parameters
    ----------
    context
       The context in which the completion should be rendered.

    name
       The name of the option, as it appears in an rst file.

    directive
       The name of the directive, as it appears in an rst file.

    implementation
       The class implementing the directive.

    Returns
    -------
    Optional[CompletionItem]
       The final completion item or ``None``.
       If ``None`` is returned, the given completion should be skipped.
    """

    if context.config.preferred_insert_behavior == "insert":
        return _render_directive_option_with_insert_text(
            context, name, directive, implementation
        )

    return _render_directive_option_with_text_edit(
        context, name, directive, implementation
    )


def _render_directive_with_insert_text(
    context: CompletionContext,
    name: str,
    directive: Type[Directive],
) -> Optional[CompletionItem]:
    """Render a ``CompletionItem`` using ``insertText`` fields.

    This implements the ``insert`` behavior for directives.
    Parameters
    ----------
    context
       The context in which the completion is being generated.

    name
       The name of the directive, as it appears in an rst file.

    directive
       The class implementing the directive.

    """
    insert_text = f".. {name}::"
    user_text = context.match.group(0).strip()

    # Since we can't replace any existing text, it only makes sense
    # to offer completions that ailgn with what the user has already written.
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

    item = _render_directive_common(name, directive)
    item.insert_text = insert_text[start_index:]
    return item


def _render_directive_with_text_edit(
    context: CompletionContext,
    name: str,
    directive: Type[Directive],
) -> Optional[CompletionItem]:
    """Render a directive's ``CompletionItem`` using the ``textEdit`` field.

    This implements the ``replace`` insert behavior for directives.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    name
       The name of the directive, as it appears in an rst file.

    directive
       The class implementing the directive.

    """
    match = context.match

    # Calculate the range of text the CompletionItems should edit.
    # If there is an existing argument to the directive, we should leave it untouched
    # otherwise, edit the whole line to insert any required arguments.
    start = match.span()[0] + match.group(0).find(".")
    include_argument = context.snippet_support
    end = match.span()[1]

    if match.group("argument"):
        include_argument = False
        end = match.span()[0] + match.group(0).find("::") + 2

    range_ = Range(
        start=Position(line=context.position.line, character=start),
        end=Position(line=context.position.line, character=end),
    )

    # TODO: Give better names to arguments based on what they represent.
    if include_argument:
        insert_format = InsertTextFormat.Snippet
        nargs = getattr(directive, "required_arguments", 0)
        args = " " + " ".join("${{{0}:arg{0}}}".format(i) for i in range(1, nargs + 1))
    else:
        args = ""
        insert_format = InsertTextFormat.PlainText

    insert_text = f".. {name}::{args}"

    item = _render_directive_common(name, directive)
    item.filter_text = insert_text
    item.text_edit = TextEdit(range=range_, new_text=insert_text)
    item.insert_text_format = insert_format

    return item


def _render_directive_common(
    name: str,
    directive: Type[Directive],
) -> CompletionItem:
    """Render the common fields of a directive's completion item."""

    try:
        dotted_name = f"{directive.__module__}.{directive.__name__}"
    except AttributeError:
        dotted_name = f"{directive.__module__}.{directive.__class__.__name__}"

    return CompletionItem(
        label=name,
        detail=dotted_name,
        kind=CompletionItemKind.Class,
        data={"completion_type": "directive"},
    )


def _render_directive_option_with_insert_text(
    context: CompletionContext,
    name: str,
    directive: str,
    implementation: Type[Directive],
) -> Optional[CompletionItem]:
    """Render a directive option's ``CompletionItem`` using the ``insertText`` field.

    This implements the ``insert`` insert behavior for directive options.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    name
       The name of the directive option, as it appears in an rst file.

    directive
       The name of the directive, as it appears in an rst file.

    implementation
       The class implementing the directive.

    """

    insert_text = f":{name}:"
    user_text = context.match.group(0).strip()

    if not insert_text.startswith(user_text):
        return None

    if user_text.endswith((":", "-", " ")):
        start_index = len(user_text)

    else:
        start_indices = [m.start() for m in WORD.finditer(user_text)] or [
            len(user_text)
        ]
        start_index = max(start_indices)

    item = _render_directive_option_common(name, directive, implementation)
    item.insert_text = insert_text[start_index:]
    return item


def _render_directive_option_with_text_edit(
    context: CompletionContext,
    name: str,
    directive: str,
    implementation: Type[Directive],
) -> CompletionItem:
    """Render a directive option's ``CompletionItem`` using the``textEdit`` field.

    This implements the ``replace`` insert behavior for directive options.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    name
       The name of the directive option, as it appears in an rst file.

    directive
       The name of the directive, as it appears in an rst file.

    implementation
       The class implementing the directive.

    """

    match = context.match
    groups = match.groupdict()

    option = groups["option"]
    start = match.span()[0] + match.group(0).find(option)
    end = start + len(option)

    range_ = Range(
        start=Position(line=context.position.line, character=start),
        end=Position(line=context.position.line, character=end),
    )

    insert_text = f":{name}:"

    item = _render_directive_option_common(name, directive, implementation)
    item.filter_text = insert_text
    item.text_edit = TextEdit(range=range_, new_text=insert_text)

    return item


def _render_directive_option_common(
    name: str, directive: str, impl: Type[Directive]
) -> CompletionItem:
    """Render the common fields of a directive option's completion item."""

    try:
        impl_name = f"{impl.__module__}.{impl.__name__}"
    except AttributeError:
        impl_name = f"{impl.__module__}.{impl.__class__.__name__}"

    return CompletionItem(
        label=name,
        detail=f"{impl_name}:{name}",
        kind=CompletionItemKind.Field,
        data={"completion_type": "directive_option", "for_directive": directive},
    )
