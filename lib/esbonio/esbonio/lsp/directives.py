import re
import traceback
import typing
import warnings
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from docutils.parsers.rst import Directive
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
from typing_extensions import Protocol

from esbonio.lsp import CompletionContext
from esbonio.lsp import DefinitionContext
from esbonio.lsp import DocumentLinkContext
from esbonio.lsp import HoverContext
from esbonio.lsp import ImplementationContext
from esbonio.lsp import LanguageFeature
from esbonio.lsp import RstLanguageServer
from esbonio.lsp.sphinx import SphinxLanguageServer
from esbonio.lsp.util.inspect import get_object_location
from esbonio.lsp.util.patterns import DIRECTIVE
from esbonio.lsp.util.patterns import DIRECTIVE_OPTION


class DirectiveLanguageFeature:
    """Base class for directive language features."""

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
        return []

    def get_implementation(
        self, directive: str, domain: Optional[str]
    ) -> Optional[Directive]:
        """Return the implementation for the given directive name."""
        return self.index_directives().get(directive, None)

    def index_directives(self) -> Dict[str, Directive]:
        """Return all known directives."""
        return dict()

    def suggest_directives(
        self, context: CompletionContext
    ) -> Iterable[Tuple[str, Directive]]:
        """Suggest directives that may be used, given a completion context."""
        return self.index_directives().items()

    def suggest_options(
        self, context: CompletionContext, directive: str, domain: Optional[str]
    ) -> Iterable[str]:
        """Suggest options that may be used, given a completion context."""

        impl = self.get_implementation(directive, domain)
        if impl is None:
            return []

        option_spec = impl.option_spec or {}
        return option_spec.keys()

    def resolve_argument_link(
        self,
        context: DocumentLinkContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Resolve a document link request for the given argument.

        Parameters
        ----------
        context
           The context of the document link request.

        directive
           The name of the directive the argument is associated with.

        domain
           The name of the domain the directive belongs to, if applicable.

        argument
           The argument to resolve the link for.
        """
        return None, None

    def find_argument_definitions(
        self,
        context: DefinitionContext,
        directive: str,
        domain: Optional[str],
        argument: str,
    ) -> List[Location]:
        """Return a list of locations representing definitions of the given argument.

        Parameters
        ----------
        context
           The context of the definition request.

        directive
           The name of the directive the argument is associated with.

        domain
           The name of the domain the directive belongs to, if applicable.

        argument
           The argument to find the definition of.
        """
        return []


class ArgumentCompletion(Protocol):
    """A completion provider for directive arguments.

    .. deprecated:: 0.14.2

       This will be removed in ``v1.0``, use subclasses of
       :class:`~esbonio.lsp.directives.DirectiveLanguageFeature` instead.
    """

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
    """A definition provider for directive arguments.

    .. deprecated:: 0.14.2

       This will be removed in ``v1.0``, use subclasses of
       :class:`~esbonio.lsp.directives.DirectiveLanguageFeature` instead.
    """

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
    """A document link resolver for directive arguments.

    .. deprecated:: 0.14.2

       This will be removed in ``v1.0``, use subclasses of
       :class:`~esbonio.lsp.directives.DirectiveLanguageFeature` instead.
    """

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

        self._features: Dict[str, DirectiveLanguageFeature] = {}
        """The collection of registered features."""

    def add_feature(self, feature: DirectiveLanguageFeature):
        """Register a directive language feature.

        Parameters
        ----------
        feature
           The directive language feature
        """
        key = f"{feature.__module__}.{feature.__class__.__name__}"

        # Create an unique key for this instance.
        if key in self._features:
            key += f".{len([k for k in self._features.keys() if k.startswith(key)])}"

        self._features[key] = feature

    def add_argument_completion_provider(self, provider: ArgumentCompletion) -> None:
        """Register an :class:`~esbonio.lsp.directives.ArgumentCompletion` provider.

        .. deprecated:: 0.14.2

           This will be removed in ``v1.0``, use
           :meth:`~esbonio.lsp.directives.Directives.add_feature` with a
           :class:`~esbonio.lsp.directives.DirectiveLanguageFeature` subclass instead.

        Parameters
        ----------
        provider:
           The provider to register.
        """
        warnings.warn(
            "ArgumentCompletion providers are deprecated in favour of "
            "DirectiveLanguageFeatures, this method will be removed in v1.0",
            DeprecationWarning,
            stacklevel=2,
        )

        name = provider.__class__.__name__
        key = f"{provider.__module__}.{name}.completion"

        # Automatically derive the feature definition from the provider.
        feature = type(
            f"{name}CompletionProvider",
            (DirectiveLanguageFeature,),
            {"complete_arguments": provider.complete_arguments},
        )()

        self._features[key] = feature

    def add_argument_definition_provider(self, provider: ArgumentDefinition) -> None:
        """Register an :class:`~esbonio.lsp.directives.ArgumentDefinition` provider.

        .. deprecated:: 0.14.2

           This will be removed in ``v1.0``, use
           :meth:`~esbonio.lsp.directives.Directives.add_feature` with a
           :class:`~esbonio.lsp.directives.DirectiveLanguageFeature` subclass instead.

        Parameters
        ----------
        provider:
           The provider to register.
        """
        warnings.warn(
            "ArgumentDefinition providers are deprecated in favour of "
            "DirectiveLanguageFeatures, this method will be removed in v1.0",
            DeprecationWarning,
            stacklevel=2,
        )

        name = provider.__class__.__name__
        key = f"{provider.__module__}.{name}.definitions"

        # Automatically derive the feature definition from the provider.
        feature = type(
            f"{name}DefinitionProvider",
            (DirectiveLanguageFeature,),
            {"find_argument_definitions": provider.find_definitions},
        )()

        self._features[key] = feature

    def add_argument_link_provider(self, provider: ArgumentLink) -> None:
        """Register an :class:`~esbonio.lsp.directives.ArgumentLink` provider.

        .. deprecated:: 0.14.2

           This will be removed in ``v1.0``, use
           :meth:`~esbonio.lsp.directives.Directives.add_feature` with a
           :class:`~esbonio.lsp.directives.DirectiveLanguageFeature` subclass instead.

        Parameters
        ----------
        provider:
           The provider to register.
        """
        warnings.warn(
            "ArgumentLink providers are deprecated in favour of "
            "DirectiveLanguageFeatures, this method will be removed in v1.0",
            DeprecationWarning,
            stacklevel=2,
        )

        name = provider.__class__.__name__
        key = f"{provider.__module__}.{name}.links"

        # Automatically derive the feature definition from the provider.
        feature = type(
            f"{name}LinkProvider",
            (DirectiveLanguageFeature,),
            {"resolve_argument_link": provider.resolve_link},
        )()

        self._features[key] = feature

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

    def get_directives(self) -> Dict[str, Directive]:
        """Return a dictionary of all known directives."""

        directives = {}

        for name, feature in self._features.items():
            try:
                directives.update(feature.index_directives())
            except Exception:
                self.logger.error(
                    "Unable to index directives, error in feature '%s'\n%s",
                    name,
                    traceback.format_exc(),
                )

        return directives

    def get_implementation(
        self, directive: str, domain: Optional[str]
    ) -> Optional[Directive]:
        """Return the implementation of a directive given its name

        Parameters
        ----------
        directive
           The name of the directive.

        domain
           The domain of the directive, if applicable.
        """

        if domain:
            name = f"{domain}:{directive}"
        else:
            name = directive

        for feature_name, feature in self._features.items():
            try:
                impl = feature.get_implementation(directive, domain)
                if impl is not None:
                    return impl
            except Exception:
                self.logger.error(
                    "Unable to get implementation for '%s', error in feature: '%s'\n%s",
                    name,
                    feature_name,
                    traceback.format_exc(),
                )

        self.logger.debug(
            "Unable to get implementation for '%s', unknown directive", name
        )
        return None

    def suggest_directives(
        self, context: CompletionContext
    ) -> Iterable[Tuple[str, Directive]]:
        """Suggest directives that may be used, given a completion context.

        Parameters
        ----------
        context
           The CompletionContext.
        """

        for name, feature in self._features.items():
            try:
                yield from feature.suggest_directives(context)
            except Exception:
                self.logger.error(
                    "Unable to suggest directives, error in feature: '%s'\n%s",
                    name,
                    traceback.format_exc(),
                )

    def suggest_options(
        self, context: CompletionContext, directive: str, domain: Optional[str]
    ) -> Iterable[str]:
        """Suggest directive options that may be used, given a completion context."""

        if domain:
            name = f"{domain}:{directive}"
        else:
            name = directive

        for feature_name, feature in self._features.items():
            try:
                yield from feature.suggest_options(context, directive, domain)
            except Exception:
                self.logger.error(
                    "Unable to suggest options for directive '%s', error in feature: '%s'\n%s",
                    name,
                    feature_name,
                    traceback.format_exc(),
                )

    completion_triggers = [DIRECTIVE, DIRECTIVE_OPTION]
    definition_triggers = [DIRECTIVE]
    hover_triggers = [DIRECTIVE]
    implementation_triggers = [DIRECTIVE]

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

        for feature in self._features.values():
            arguments += feature.complete_arguments(context, domain, name) or []

        return arguments

    def complete_directives(self, context: CompletionContext) -> List[CompletionItem]:
        self.logger.debug("Completing directives")

        items = []
        match = context.match
        groups = match.groupdict()

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

        for name, directive in self.suggest_directives(context):

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

        surrounding_directive = self._get_surrounding_directive(context)
        if not surrounding_directive:
            return []

        name = surrounding_directive.group("name")
        domain = surrounding_directive.group("domain")
        impl = self.get_implementation(name, domain)
        if impl is None:
            return []

        items = []
        match = context.match
        groups = match.groupdict()
        impl_name = f"{impl.__module__}.{impl.__name__}"

        option = groups["option"]
        start = match.span()[0] + match.group(0).find(option)
        end = start + len(option)

        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )

        for option in self.suggest_options(context, name, domain):
            insert_text = f":{option}:"

            items.append(
                CompletionItem(
                    label=option,
                    detail=f"{impl_name}:{option}",
                    kind=CompletionItemKind.Field,
                    filter_text=insert_text,
                    text_edit=TextEdit(range=range_, new_text=insert_text),
                    data={
                        "completion_type": "directive_option",
                        "for_directive": name,
                    },
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

    def definition(self, context: DefinitionContext) -> List[Location]:

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

        for feature_name, feature in self._features.items():
            try:
                definitions += (
                    feature.find_argument_definitions(
                        context, directive, domain, argument
                    )
                    or []
                )
            except Exception:
                self.logger.error(
                    "Unable to find definitions of '%s' for directive '%s', "
                    "error in feature: '%s'",
                    argument,
                    f"{domain}:{directive}" if domain else directive,
                    feature_name,
                    exc_info=True,
                )

        return definitions

    def resolve_argument_link(
        self, context: DocumentLinkContext, name: str, domain: str, argument: str
    ) -> Tuple[Optional[str], Optional[str]]:

        for feature_name, feature in self._features.items():
            try:
                target, tooltip = feature.resolve_argument_link(
                    context, name, domain, argument
                )

                if target:
                    return target, tooltip
            except Exception:
                self.logger.error(
                    "Unable to resolve argument link '%s' for directive '%s', "
                    "error in feature: '%s'",
                    argument,
                    f"{domain}:{name}" if domain else name,
                    feature_name,
                    exc_info=True,
                )

        return None, None

    def document_link(self, context: DocumentLinkContext) -> List[DocumentLink]:
        links = []

        for line, text in enumerate(context.doc.lines):
            for match in DIRECTIVE.finditer(text):

                argument = match.group("argument")
                if not argument:
                    continue

                domain = match.group("domain")
                name = match.group("name")

                target, tooltip = self.resolve_argument_link(
                    context, name, domain, argument
                )
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

    def hover(self, context: HoverContext) -> str:

        if context.location not in {"rst", "docstring"}:
            return ""

        name = context.match.group("name")
        domain = context.match.group("domain")

        # Determine if the hover is on the .. directive::  itself, or within the argument
        # Be sure to include enough chars for the length of '::'!
        idx = context.position.character - context.match.start()
        prefix = context.match.group(0)[:idx]

        if "::" not in prefix:
            return self.hover_directive(context, name, domain)

        # TODO: Add extension points for directive arguments and options.
        return ""

    def hover_directive(
        self, context: HoverContext, name: str, domain: Optional[str]
    ) -> str:

        label = f"{domain}:{name}" if domain else name
        self.logger.debug("Calculating hover for directive '%s'", label)

        directive = self.get_implementation(name, domain)
        if not directive:
            return ""

        try:
            dotted_name = f"{directive.__module__}.{directive.__name__}"
        except AttributeError:
            dotted_name = f"{directive.__module__}.{directive.__class__.__name__}"

        documentation = self.get_documentation(label, dotted_name)
        if not documentation:
            return ""

        return documentation.get("description", "")

    def implementation(self, context: ImplementationContext) -> List[Location]:

        region = context.match.group("directive")
        name = context.match.group("name")
        domain = context.match.group("domain")

        start = context.match.group(0).index(region)
        end = start + len(region)

        if start <= context.position.character <= end:
            return self.find_directive_implementation(context, name, domain)

        return []

    def find_directive_implementation(
        self, context: ImplementationContext, name: str, domain: Optional[str]
    ) -> List[Location]:

        impl = self.get_implementation(name, domain)
        if impl is None:
            return []

        self.logger.debug(
            "Getting implementation of '%s' (%s)",
            f"{domain}:{name}" if domain else name,
            impl,
        )
        location = get_object_location(impl, self.logger)
        if location is None:
            return []

        return [location]

    def _get_surrounding_directive(
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
    rst.add_feature(Directives(rst))
