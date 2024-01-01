import inspect
import re
from typing import Dict
from typing import List
from typing import Optional

import attrs
from lsprotocol import types

from esbonio import server
from esbonio.sphinx_agent.types import RST_DIRECTIVE


@attrs.define
class Directive:
    """Represents a directive."""

    name: str
    """The name of the directive, as the user would type in an rst file."""

    implementation: Optional[str]
    """The dotted name of the directive's implementation."""


class DirectiveProvider:
    """Base class for directive providers"""

    def suggest_directives(
        self, context: server.CompletionContext
    ) -> Optional[List[Directive]]:
        """Given a completion context, suggest directives that may be used."""
        return None


class DirectiveFeature(server.LanguageFeature):
    """reStructuredText directive support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._providers: Dict[int, DirectiveProvider] = {}

    def add_provider(self, provider: DirectiveProvider):
        """Register a directive provider.

        Parameters
        ----------
        provider
           The directive provider
        """
        self._providers[id(provider)] = provider

    completion_triggers = [RST_DIRECTIVE]

    async def completion(
        self, context: server.CompletionContext
    ) -> Optional[List[types.CompletionItem]]:
        """Provide auto-completion suggestions for directives."""

        groups = context.match.groupdict()

        # Are we completing a directive's options?
        if "directive" not in groups:
            return await self.complete_options(context)

        # Are we completing the directive's argument?
        directive_end = context.match.span()[0] + len(groups["directive"])
        complete_directive = groups["directive"].endswith("::")

        if complete_directive and directive_end < context.position.character:
            return await self.complete_arguments(context)

        return await self.complete_directives(context)

    async def complete_options(self, context: server.CompletionContext):
        return None

    async def complete_arguments(self, context: server.CompletionContext):
        return None

    async def complete_directives(self, context: server.CompletionContext):
        items = []

        for directive in await self.suggest_directives(context):
            if (item := render_directive_completion(context, directive)) is not None:
                items.append(item)

        if len(items) > 0:
            return items

    async def suggest_directives(
        self, context: server.CompletionContext
    ) -> List[Directive]:
        """Suggest directives that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context.
        """
        items = []

        for provider in self._providers.values():
            try:
                result = provider.suggest_directives(context)
                if inspect.isawaitable(result):
                    result = await result

                if result:
                    items.extend(result)
            except Exception:
                name = type(provider).__name__
                self.logger.error(
                    "Error in '%s.suggest_directives'", name, exc_info=True
                )

        return items


WORD = re.compile("[a-zA-Z]+")


def render_directive_completion(
    context: server.CompletionContext, directive: Directive
) -> Optional[types.CompletionItem]:
    """Render the given directive as a ``CompletionItem`` according to the current
    context.

    Parameters
    ----------
    context
       The context in which the completion should be rendered.

    directive
       The directive to render

    Returns
    -------
    Optional[CompletionItem]
       The final completion item or ``None``.
       If ``None`` is returned, then the given completion should be skipped.
    """

    # TODO: Bring this back
    # if context.config.preferred_insert_behavior == "insert":
    #     return _render_directive_with_insert_text(context, name, directive)

    return _render_directive_with_text_edit(context, directive)


def _render_directive_with_insert_text(
    context: server.CompletionContext,
    directive: Directive,
) -> Optional[types.CompletionItem]:
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
    insert_text = f".. {directive.name}::"
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

    item = _render_directive_common(directive)
    item.insert_text = insert_text[start_index:]
    return item


def _render_directive_with_text_edit(
    context: server.CompletionContext,
    directive: Directive,
) -> Optional[types.CompletionItem]:
    """Render a directive's ``CompletionItem`` using the ``textEdit`` field.

    This implements the ``replace`` insert behavior for directives.

    Parameters
    ----------
    context
       The context in which the completion is being generated.

    directive
       The directive to render.

    """
    match = context.match

    # Calculate the range of text the CompletionItems should edit.
    # If there is an existing argument to the directive, we should leave it untouched
    # otherwise, edit the whole line to insert any required arguments.
    start = match.span()[0] + match.group(0).find(".")

    if match.group("argument"):
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


def esbonio_setup(server: server.EsbonioLanguageServer):
    directives = DirectiveFeature(server)
    server.add_feature(directives)
