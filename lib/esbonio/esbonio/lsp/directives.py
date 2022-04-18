"""Logic around directive completions goes here."""
import json
import re
import typing
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import pkg_resources
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import DocumentLink
from pygls.lsp.types import InsertTextFormat
from pygls.lsp.types import Location
from pygls.lsp.types import MarkupContent
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import TextEdit

from esbonio.lsp import CompletionContext
from esbonio.lsp import DefinitionContext
from esbonio.lsp import DocumentLinkContext
from esbonio.lsp import LanguageFeature
from esbonio.lsp import RstLanguageServer
from esbonio.lsp.sphinx import SphinxLanguageServer

try:
    from typing import Protocol
except ImportError:
    # Protocol is only available in Python 3.8+
    class Protocol:  # type: ignore
        ...


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


class ArgumentCompletion(Protocol):
    """A completion provider for directive arguments."""

    def complete_arguments(
        self, context: CompletionContext, domain: str, name: str
    ) -> List[CompletionItem]:
        """Return a list of completion items representing valid targets for the given
        directive.

        Parameters
        ----------
        context:
           The completion context
        domain:
           The name of the domain the directive is a member of
        name:
           The name of the domain
        """


class ArgumentDefinition(Protocol):
    """A definition provider for directive arguments."""

    def find_definitions(
        self,
        context: DefinitionContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> List[Location]:
        """Return a list of locations representing definitions of the given argument.

        Parameters
        ----------
        context:
           The context of the definition request.
        directive:
           The name of the directive the argument is associated with.
        domain:
           The name of the domain the directive belongs to, if applicable.
        argument:
           The argument to find the definition of.
        """


class ArgumentLink(Protocol):
    """A document link resolver for directive arguments."""

    def resolve_link(
        self,
        context: DocumentLinkContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Resolve a document link request for the given argument.

        Parameters
        ----------
        context:
           The context of the document link request.
        directive:
           The name of the directive the argument is associated with.
        domain:
           The name of the domain the directive belongs to, if applicable.
        argument:
           The argument to resolve the link for.
        """


class Directives(LanguageFeature):
    """Directive support for the language server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._documentation: Dict[str, Dict[str, str]] = {}
        """Cache for documentation."""

        self._argument_completion_providers: Dict[str, ArgumentCompletion] = {}
        """A dictionary of providers that give completion suggestions for directive
        arguments."""

        self._argument_definition_providers: Dict[str, ArgumentDefinition] = {}
        """A dictionary of providers that locate definitions for directive arguments."""

        self._argument_link_providers: Dict[str, ArgumentLink] = {}
        """A dictionary of providers that resolve document links for directive
        arguments."""

    def add_argument_completion_provider(self, provider: ArgumentCompletion) -> None:
        """Register an :class:`~esbonio.lsp.directives.ArgumentCompletion` provider.

        Parameters
        ----------
        provider:
           The provider to register.
        """
        key = f"{provider.__module__}.{provider.__class__.__name__}"
        self._argument_completion_providers[key] = provider

    def add_argument_definition_provider(self, provider: ArgumentDefinition) -> None:
        """Register an :class:`~esbonio.lsp.directives.ArgumentDefinition` provider.

        Parameters
        ----------
        provider:
           The provider to register.
        """
        key = f"{provider.__module__}.{provider.__class__.__name__}"
        self._argument_definition_providers[key] = provider

    def add_argument_link_provider(self, provider: ArgumentLink) -> None:
        """Register an :class:`~esbonio.lsp.directives.ArgumentLink` provider.

        Parameters
        ----------
        provider:
           The provider to register.
        """
        key = f"{provider.__module__}.{provider.__class__.__name__}"
        self._argument_link_providers[key] = provider

    def add_documentation(self, documentation: Dict[str, Dict[str, Any]]) -> None:
        """Register directive documentation.

        ``documentation`` should be a dictionary with the following structure ::

           documentation = {
               "raw(docutils.parsers.rst.directives.misc.Raw)": {
                   "is_markdown": true,
                   "license": "https://...",
                   "source": "https://...",
                   "description": [
                       "# .. raw::",
                       "The raw directive is used for...",
                       ...
                    ]
                   "options": {
                       "file": "The file option allows...",
                       ...
                   }
               }
           }

        where the key has the form ``name(dotted_name)``. There are cases where a
        directive's implementation is not sufficient to uniquely identify it as
        multiple directives can be provided by a single class.

        This means the key has to be a combination of the ``name`` the user writes
        in a reStructuredText document and ``dotted_name`` is the fully qualified
        class name of the directive's implementation.

        .. note::

           If there is a clash with an existing key, the existing value will be
           overwritten with the new value.

        The values in this dictionary are themselves dictionaries with the following
        fields.

        ``description``
           A list of strings for the directive's main documentation.

        ``options``,
           A dictionary, with a field for the documentaton of each of the directive's
           options.

        ``is_markdown``
           A boolean flag used to indicate whether the ``description`` and ``options``
           are written in plain text or markdown.

        ``source``
           The url to the documentation's source

        ``license``
           The url to the documentation's license

        Parameters
        ----------
        documentation:
           The documentation to register.
        """

        for key, doc in documentation.items():
            description = doc.get("description", [])

            if not description:
                continue

            source = doc.get("source", "")
            if source:
                description.append(f"\n[Source]({source})")

            license = doc.get("license", "")
            if license:
                description.append(f"\n[License]({license})")

            doc["description"] = "\n".join(description)
            self._documentation[key] = doc

    completion_triggers = [DIRECTIVE, DIRECTIVE_OPTION]

    def completion_resolve(self, item: CompletionItem) -> CompletionItem:

        # We need extra info to know who to call.
        if not item.data:
            return item

        data = typing.cast(Dict, item.data)
        ctype = data.get("completion_type", "")

        if ctype == "directive":
            return self.completion_resolve_directive(item)

        if ctype == "directive_option":
            return self.completion_resolve_option(item)

        return item

    def complete(self, context: CompletionContext) -> List[CompletionItem]:

        # Do not suggest completions within the middle of Python code.
        if context.location == "py":
            return []

        groups = context.match.groupdict()

        # Are we completing a directive's options?
        if "directive" not in groups:
            return self.complete_options(context)

        # Are we completing the directive's argument?
        directive_end = context.match.span()[0] + len(groups["directive"])
        complete_directive = groups["directive"].endswith("::")

        if complete_directive and directive_end < context.position.character:
            return self.complete_arguments(context)

        return self.complete_directives(context)

    def complete_arguments(self, context: CompletionContext) -> List[CompletionItem]:
        arguments = []
        name = context.match.group("name")
        domain = context.match.group("domain") or ""

        for provider_name, provider in self._argument_completion_providers.items():
            arguments += provider.complete_arguments(context, domain, name) or []

        return arguments

    def complete_directives(self, context: CompletionContext) -> List[CompletionItem]:
        self.logger.debug("Completing directives")

        items = []
        match = context.match
        groups = match.groupdict()

        domain = ""
        if groups["domain"]:
            domain = f'{groups["domain"]}:'

        # Calculate the range of text the CompletionItems should edit.
        # If there is an existing argument to the directive, we should leave it untouched
        # otherwise, edit the whole line to insert any required arguments.
        start = match.span()[0] + match.group(0).find(".")
        include_argument = context.snippet_support
        end = match.span()[1]

        if groups["argument"]:
            include_argument = False
            end = match.span()[0] + match.group(0).find("::") + 2

        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )

        for name, directive in self.rst.get_directives().items():

            if not name.startswith(domain):
                continue

            # TODO: Give better names to arguments based on what they represent.
            if include_argument:
                insert_format = InsertTextFormat.Snippet
                args = " " + " ".join(
                    "${{{0}:arg{0}}}".format(i)
                    for i in range(1, directive.required_arguments + 1)
                )
            else:
                args = ""
                insert_format = InsertTextFormat.PlainText

            try:
                dotted_name = f"{directive.__module__}.{directive.__name__}"
            except AttributeError:
                dotted_name = f"{directive.__module__}.{directive.__class__.__name__}"

            insert_text = f".. {name}::{args}"

            items.append(
                CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Class,
                    detail=dotted_name,
                    filter_text=insert_text,
                    text_edit=TextEdit(range=range_, new_text=insert_text),
                    insert_text_format=insert_format,
                    data={"completion_type": "directive"},
                )
            )

        return items

    def completion_resolve_directive(self, item: CompletionItem) -> CompletionItem:

        # We need the detail field set to the implementation's fully qualified name.
        if not item.detail:
            return item

        documentation = self.get_documentation(item.label, item.detail)
        if not documentation:
            return item

        description = documentation.get("description", "")
        is_markdown = documentation.get("is_markdown", False)
        kind = MarkupKind.Markdown if is_markdown else MarkupKind.PlainText

        item.documentation = MarkupContent(kind=kind, value=description)
        return item

    def complete_options(self, context: CompletionContext) -> List[CompletionItem]:

        surrounding_directive = self.get_surrounding_directive(context)
        if not surrounding_directive:
            return []

        domain = ""
        if surrounding_directive.group("domain"):
            domain = f'{surrounding_directive.group("domain")}:'

        name = f"{domain}{surrounding_directive.group('name')}"
        directive = self.rst.get_directives().get(name, None)

        if not directive:
            return []

        items = []
        match = context.match
        groups = match.groupdict()

        option = groups["option"]
        start = match.span()[0] + match.group(0).find(option)
        end = start + len(option)

        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )

        for option in self.rst.get_directive_options(name):
            insert_text = f":{option}:"

            items.append(
                CompletionItem(
                    label=option,
                    detail=f"{directive.__module__}.{directive.__name__}:{option}",
                    kind=CompletionItemKind.Field,
                    filter_text=insert_text,
                    text_edit=TextEdit(range=range_, new_text=insert_text),
                    data={"completion_type": "directive_option", "for_directive": name},
                )
            )

        return items

    def completion_resolve_option(self, item: CompletionItem) -> CompletionItem:

        # We need the detail field set to the implementation's fully qualified name.
        if not item.detail or not item.data:
            return item

        directive, option = item.detail.split(":")
        name = typing.cast(Dict, item.data).get("for_directive", "")

        documentation = self.get_documentation(name, directive)
        if not documentation:
            return item

        description = documentation.get("options", {}).get(option, None)
        if not description:
            return item

        source = documentation.get("source", "")
        license = documentation.get("license", "")

        if source:
            description += f"\n\n[Source]({source})"

        if license:
            description += f"\n\n[License]({license})"

        kind = MarkupKind.PlainText
        if documentation.get("is_markdown", False):
            kind = MarkupKind.Markdown

        item.documentation = MarkupContent(kind=kind, value=description)
        return item

    definition_triggers = [DIRECTIVE]

    def definition(self, context: DefinitionContext) -> List[Location]:
        self.rst.logger.debug("%s", context)

        directive = context.match.group("name")
        domain = context.match.group("domain")
        argument = context.match.group("argument")

        if not argument:
            return []

        start = context.match.group(0).index(argument)
        end = start + len(argument)

        if start <= context.position.character <= end:
            return self.find_argument_definition(context, directive, domain, argument)

        return []

    def find_argument_definition(
        self,
        context: DefinitionContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> List[Location]:
        definitions = []

        for _, provider in self._argument_definition_providers.items():
            definitions += (
                provider.find_definitions(context, directive, domain, argument) or []
            )

        return definitions

    def document_link(self, context: DocumentLinkContext) -> List[DocumentLink]:
        links = []

        for line, text in enumerate(context.doc.lines):
            for match in DIRECTIVE.finditer(text):

                argument = match.group("argument")
                if not argument:
                    continue

                domain = match.group("domain")
                name = match.group("name")

                target = None
                tooltip = None
                for provider in self._argument_link_providers.values():
                    target, tooltip = provider.resolve_link(
                        context, name, domain, argument
                    )
                    if target:
                        break

                if not target:
                    continue

                idx = match.group(0).index(argument)
                start = match.start() + idx
                end = start + len(argument)

                links.append(
                    DocumentLink(
                        target=target,
                        tooltip=tooltip if context.tooltip_support else None,
                        range=Range(
                            start=Position(line=line, character=start),
                            end=Position(line=line, character=end),
                        ),
                    )
                )

        return links

    def get_surrounding_directive(
        self, context: CompletionContext
    ) -> Optional["re.Match"]:
        """Used to determine which directive we should be offering completions for.

        When suggestions should be generated this returns an :class:`python:re.Match`
        object representing the directive the options are associated with. In the
        case where suggestions should not be generated this will return ``None``

        Parameters
        ----------
        context:
          The completion context
        """

        match = context.match
        groups = match.groupdict()
        indent = groups["indent"]

        self.logger.debug("Match groups: %s", groups)

        # Search backwards so that we can determine the context for our completion
        linum = context.position.line - 1
        line = context.doc.lines[linum]

        while linum >= 0 and line.startswith(indent):
            linum -= 1
            line = context.doc.lines[linum]

        # Only offer completions if we're within a directive's option block
        directive = DIRECTIVE.match(line)
        self.logger.debug("Context line:  %s", line)
        self.logger.debug("Context match: %s", directive)

        if not directive:
            return None

        # Now that we know we're in a directive's option block, is the completion
        # request coming from a valid position on the line?
        option = groups["option"]
        start = match.span()[0] + match.group(0).find(option)
        end = start + len(option) + 1

        if start <= context.position.character <= end:
            return directive

        return None

    def get_documentation(
        self, label: str, implementation: str
    ) -> Optional[Dict[str, Any]]:
        """Return the documentation for the given directive, if available.

        If documentation for the given ``label`` cannot be found, this function will also
        look for the label under the project's :confval:`sphinx:primary_domain` followed
        by the ``std`` domain.

        Parameters
        ----------
        label
           The name of the directive, as the user would type in an reStructuredText file.

        implementation
           The full dotted name of the directive's implementation.
        """

        key = f"{label}({implementation})"
        documentation = self._documentation.get(key, None)
        if documentation:
            return documentation

        if not isinstance(self.rst, SphinxLanguageServer) or not self.rst.app:
            return None

        # Nothing found, try the primary domain
        domain = self.rst.app.config.primary_domain
        key = f"{domain}:{label}({implementation})"

        documentation = self._documentation.get(key, None)
        if documentation:
            return documentation

        # Still nothing, try the standard domain
        key = f"std:{label}({implementation})"

        documentation = self._documentation.get(key, None)
        if documentation:
            return documentation

        return None


def esbonio_setup(rst: RstLanguageServer):
    """Configure and reigster the directives feature with the server."""

    directives = Directives(rst)
    rst.add_feature(directives)

    docutils_docs = pkg_resources.resource_string("esbonio.lsp.rst", "directives.json")
    directives.add_documentation(json.loads(docutils_docs.decode("utf8")))

    if isinstance(rst, SphinxLanguageServer):
        sphinx_docs = pkg_resources.resource_string(
            "esbonio.lsp.sphinx", "directives.json"
        )
        directives.add_documentation(json.loads(sphinx_docs.decode("utf8")))
