"""Helper functions for completion support."""

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

    from esbonio.sphinx_agent.types import Role

    RoleRenderer = Callable[
        [server.CompletionContext, Role], Optional[types.CompletionItem]
    ]

    RoleTargetRenderer = Callable[
        [server.CompletionContext, types.CompletionItem], Optional[types.CompletionItem]
    ]


WORD = re.compile("[a-zA-Z]+")
_ROLE_RENDERERS: Dict[Tuple[str, str], RoleRenderer] = {}
"""CompletionItem rendering functions for roles."""

_ROLE_TARGET_RENDERERS: Dict[Tuple[str, str], RoleTargetRenderer] = {}
"""CompletionItem rendering functions for role targets."""


def role_renderer(*, language: str, insert_behavior: str):
    """Define a new rendering function for roles."""

    def fn(f: RoleRenderer) -> RoleRenderer:
        _ROLE_RENDERERS[(language, insert_behavior)] = f
        return f

    return fn


def role_target_renderer(*, language: str, insert_behavior: str):
    """Define a new rendering function for role targets."""

    def fn(f: RoleTargetRenderer) -> RoleTargetRenderer:
        _ROLE_TARGET_RENDERERS[(language, insert_behavior)] = f
        return f

    return fn


def get_role_renderer(language: str, insert_behavior: str) -> Optional[RoleRenderer]:
    """Return the role renderer to use.

    Parameters
    ----------
    language
       The source language the completion item will be inserted into

    insert_behavior
       How the completion should behave when inserted.

    Returns
    -------
    Optional[RoleRenderer]
       The rendering function to use that matches the given criteria, if available.
    """
    return _ROLE_RENDERERS.get((language, insert_behavior), None)


def get_role_target_renderer(
    language: str, insert_behavior: str
) -> Optional[RoleTargetRenderer]:
    """Return the role target renderer to use.

    Parameters
    ----------
    language
       The source language the completion item will be inserted into

    insert_behavior
       How the completion should behave when inserted.

    Returns
    -------
    Optional[RoleTargetRenderer]
       The rendering function to use that matches the given criteria, if available.
    """
    return _ROLE_TARGET_RENDERERS.get((language, insert_behavior), None)


@role_renderer(language="rst", insert_behavior="insert")
def render_rst_role_with_insert_text(
    context: server.CompletionContext, role: Role
) -> Optional[types.CompletionItem]:
    """Render a ``CompletionItem`` using ``insertText``.

    This implements the ``insert`` insert behavior for roles.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    role
       The role.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item, or ``None`` if the directive should be skipped
    """

    insert_text = f":{role.name}:"
    user_text = context.match.group(0).strip()

    # Since we can't replace any existing text, it only makes sense
    # to offer completions that align with what the user has already written.
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

    item = _render_role_common(role)
    item.insert_text = insert_text[start_index:]
    item.insert_text_format = types.InsertTextFormat.PlainText
    return item


@role_target_renderer(language="rst", insert_behavior="replace")
def render_rst_target_with_text_edit(
    context: server.CompletionContext, item: types.CompletionItem
) -> Optional[types.CompletionItem]:
    """Render a ``CompletionItem`` using ``insertText``.

    This implements the ``replace`` insert behavior for role targets.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    item
       The ``CompletionItem`` representing the role target.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item, or ``None`` if the item should be skipped
    """
    return item


@role_renderer(language="markdown", insert_behavior="insert")
def render_myst_role_with_insert_text(
    context: server.CompletionContext, role: Role
) -> Optional[types.CompletionItem]:
    """Render a ``CompletionItem`` using ``insertText``.

    This implements the ``insert`` insert behavior for roles.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    role
       The role.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item, or ``None`` if the directive should be skipped
    """

    insert_text = "".join(["{", role.name, "}"])
    user_text = context.match.group(0).strip()

    # Since we can't replace any existing text, it only makes sense
    # to offer completions that align with what the user has already written.
    if not insert_text.startswith(user_text):
        return None

    # If the existing text ends with a delimiter, then we should simply remove the
    # entire prefix
    if user_text.endswith((":", "-", "{", "}", "`", " ")):
        start_index = len(user_text)

    # Look for groups of word chars, replace text until the start of the final group
    else:
        start_indices = [m.start() for m in WORD.finditer(user_text)] or [
            len(user_text)
        ]
        start_index = max(start_indices)

    item = _render_role_common(role)
    item.insert_text = insert_text[start_index:]
    item.insert_text_format = types.InsertTextFormat.PlainText
    return item


@role_renderer(language="rst", insert_behavior="replace")
def render_rst_role_with_text_edit(
    context: server.CompletionContext, role: Role
) -> Optional[types.CompletionItem]:
    """Render a role's ``CompletionItem`` using ``textEdit``.

    This implements the ``replace`` insert behavior for roles.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    role
       The role.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item, or ``None`` if the directive should be skipped
    """
    match = context.match
    groups = match.groupdict()

    # Insert text starting from the starting ':' character of the role.
    start = match.span()[0] + match.group(0).find(":")
    end = start + len(groups["role"])

    range_ = types.Range(
        start=types.Position(line=context.position.line, character=start),
        end=types.Position(line=context.position.line, character=end),
    )

    insert_text = f":{role.name}:"

    item = _render_role_common(role)
    item.filter_text = insert_text
    item.insert_text_format = types.InsertTextFormat.PlainText
    item.text_edit = types.TextEdit(range=range_, new_text=insert_text)

    return item


@role_renderer(language="markdown", insert_behavior="replace")
def render_myst_role_with_text_edit(
    context: server.CompletionContext, role: Role
) -> Optional[types.CompletionItem]:
    """Render a role's ``CompletionItem`` using ``textEdit``.

    This implements the ``replace`` insert behavior for roles.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    role
       The role.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item, or ``None`` if the directive should be skipped
    """
    match = context.match
    groups = match.groupdict()

    # Insert text starting from the starting '{' character of the role.
    start = match.span()[0] + match.group(0).find("{")
    end = start + len(groups["role"])

    range_ = types.Range(
        start=types.Position(line=context.position.line, character=start),
        end=types.Position(line=context.position.line, character=end),
    )

    insert_text = "".join(["{", role.name, "}"])

    item = _render_role_common(role)
    item.filter_text = insert_text
    item.insert_text_format = types.InsertTextFormat.PlainText
    item.text_edit = types.TextEdit(range=range_, new_text=insert_text)

    return item


@role_target_renderer(language="markdown", insert_behavior="replace")
def render_myst_target_with_text_edit(
    context: server.CompletionContext, item: types.CompletionItem
) -> Optional[types.CompletionItem]:
    """Render a ``CompletionItem`` using ``textEdit``.

    This implements the ``replace`` insert behavior for role targets.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    item
       The ``CompletionItem`` representing the role target.

    Returns
    -------
    Optional[types.CompletionItem]
       The rendered completion item, or ``None`` if the item should be skipped
    """
    return item


def _render_role_common(role: Role) -> types.CompletionItem:
    """Render the common fields of a role's completion item."""
    return types.CompletionItem(
        label=role.name,
        detail=role.implementation,
        kind=types.CompletionItemKind.Function,
        data={"completion_type": "role"},
    )
