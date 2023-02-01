import re
from typing import Any
from typing import Optional

from lsprotocol.types import CompletionItem
from lsprotocol.types import CompletionItemKind
from lsprotocol.types import Position
from lsprotocol.types import Range
from lsprotocol.types import TextEdit

from esbonio.lsp import CompletionContext

__all__ = ["render_role_completion"]


WORD = re.compile("[a-zA-Z]+")


def render_role_completion(
    context: CompletionContext,
    name: str,
    role: Any,
) -> Optional[CompletionItem]:
    """Render the given role as a ``CompletionItem`` according to the current
    context.

    Parameters
    ----------
    context
       The context in which the completion should be rendered.

    name
       The name of the role, as it appears in an rst file.

    role
       The implementation of the role.

    Returns
    -------
    Optional[CompletionItem]
       The final completion item or ``None``.
       If ``None``, then the given completion should be skipped.
    """

    if context.config.preferred_insert_behavior == "insert":
        return _render_role_with_insert_text(context, name, role)

    return _render_role_with_text_edit(context, name, role)


def _render_role_with_insert_text(context, name, role):
    """Render a role's ``CompletionItem`` using the ``insertText`` field.

    This implements the ``insert`` insert behavior for roles.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    name
       The name of the role, as it appears in an rst file.

    role
       The implementation of the role.
    """

    insert_text = f":{name}:"
    user_text = context.match.group(0).strip()

    if not insert_text.startswith(user_text):
        return None

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

    item = _render_role_common(name, role)
    item.insert_text = insert_text[start_index:]
    return item


def _render_role_with_text_edit(
    context: CompletionContext, name: str, role: Any
) -> Optional[CompletionItem]:
    """Render a role's ``CompletionItem`` using the ``textEdit`` field.

    This implements the ``replace`` insert behavior for roles.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    name
       The name of the role, as it appears in an rst file.

    role
       The implementation of the role.
    """
    match = context.match
    groups = match.groupdict()
    domain = groups["domain"] or ""

    if not name.startswith(domain):
        return None

    # Insert text starting from the starting ':' character of the role.
    start = match.span()[0] + match.group(0).find(":")
    end = start + len(groups["role"])

    range_ = Range(
        start=Position(line=context.position.line, character=start),
        end=Position(line=context.position.line, character=end),
    )

    insert_text = f":{name}:"

    item = _render_role_common(name, role)
    item.filter_text = insert_text
    item.text_edit = TextEdit(range=range_, new_text=insert_text)

    return item


def _render_role_common(name: str, role: Any) -> CompletionItem:
    """Render the common fields of a role's completion item."""

    try:
        dotted_name = f"{role.__module__}.{role.__name__}"
    except AttributeError:
        dotted_name = f"{role.__module__}.{role.__class__.__name__}"

    return CompletionItem(
        label=name,
        kind=CompletionItemKind.Function,
        detail=f"{dotted_name}",
        data={"completion_type": "role"},
    )
