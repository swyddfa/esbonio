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

__all__ = ["render_directive_completion"]


WORD = re.compile("[a-zA-Z]+")


def render_directive_completion(
    context: CompletionContext,
    name: str,
    directive: Type[Directive],
) -> Optional[CompletionItem]:
    """Render the given directive as as ``CompletionItem`` according to the current
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
    """Populate the ``textEdit`` field of a ``CompletionItem``

    This implements the ``replace`` insert behavior for directives.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    name
       The name of the directive, as it appears in an rst file.

    directive
       The class implementing the directive.

    item
       The ``CompletionItem`` to populate the fields for.

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
