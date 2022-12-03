"""Role support."""
import typing
import warnings
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import DocumentLink
from pygls.lsp.types import Location
from pygls.lsp.types import MarkupContent
from pygls.lsp.types import MarkupKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import TextEdit
from typing_extensions import Protocol

from esbonio.lsp.rst import CompletionContext
from esbonio.lsp.rst import DefinitionContext
from esbonio.lsp.rst import DocumentLinkContext
from esbonio.lsp.rst import HoverContext
from esbonio.lsp.rst import ImplementationContext
from esbonio.lsp.rst import LanguageFeature
from esbonio.lsp.rst import RstLanguageServer
from esbonio.lsp.sphinx import SphinxLanguageServer
from esbonio.lsp.util.inspect import get_object_location
from esbonio.lsp.util.patterns import DEFAULT_ROLE
from esbonio.lsp.util.patterns import DIRECTIVE
from esbonio.lsp.util.patterns import ROLE


class RoleLanguageFeature:
    """Base class for role language features."""

    def complete_targets(
        self, context: CompletionContext, name: str, domain: str
    ) -> List[CompletionItem]:
        """Return a list of completion items representing valid targets for the given
        role.

        Parameters
        ----------
        context
           The completion context

        name
           The name of the role to generate completion suggestions for.

        domain
           The name of the domain the role is a member of
        """
        return []

    def find_target_definitions(
        self, context: DefinitionContext, name: str, domain: str, label: str
    ) -> List[Location]:
        """Return a list of locations representing the definition of the given role
        target.

        Parameters
        ----------
        doc:
           The document containing the match
        match:
           The match object that triggered the definition request
        name:
           The name of the role
        domain:
           The domain the role is part of, if applicable.
        """
        return []

    def get_implementation(self, role: str, domain: str) -> Optional[Any]:
        """Return the implementation for the given role name.

        Parameters
        ----------
        role
           The name of the role

        domain
           The domain the role belongs to, if any
        """
        return self.index_roles().get(role, None)

    def index_roles(self) -> Dict[str, Any]:
        """Return all known roles."""
        return dict()

    def resolve_target_link(
        self, context: DocumentLinkContext, name: str, domain: Optional[str], label: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return a link corresponding to the given target.

        Parameters
        ----------
        context
           The document link context

        domain
           The name (if applicable) of the domain the role is a member of

        name
           The name of the role to generate completion suggestions for.

        label
           The label of the target to provide the link for
        """
        return None, None

    def suggest_roles(self, context: CompletionContext) -> Iterable[Tuple[str, Any]]:
        """Suggest roles that may be used, given a completion context."""
        return self.index_roles().items()


class TargetDefinition(Protocol):
    """A definition provider for role targets.

    .. deprecated:: 0.15.0

       This will be removed in ``v1.0``, use a subclass of
       :class:`~esbonio.lsp.roles.RoleLanguageFeature` instead.
    """

    def find_definitions(
        self, context: DefinitionContext, name: str, domain: Optional[str]
    ) -> List[Location]:
        """Return a list of locations representing the definition of the given role
        target.

        Parameters
        ----------
        doc:
           The document containing the match
        match:
           The match object that triggered the definition request
        name:
           The name of the role
        domain:
           The domain the role is part of, if applicable.
        """


class TargetCompletion(Protocol):
    """A completion provider for role targets.

    .. deprecated:: 0.15.0

       This will be removed in ``v1.0``, use a subclass of
       :class:`~esbonio.lsp.roles.RoleLanguageFeature` instead.
    """

    def complete_targets(
        self, context: CompletionContext, name: str, domain: Optional[str]
    ) -> List[CompletionItem]:
        """Return a list of completion items representing valid targets for the given
        role.

        Parameters
        ----------
        context:
           The completion context
        domain:
           The name of the domain the role is a member of
        name:
           The name of the role to generate completion suggestions for.
        """


class TargetLink(Protocol):
    """A document link provider for role targets.

    .. deprecated:: 0.15.0

       This will be removed in ``v1.0``, use a subclass of
       :class:`~esbonio.lsp.roles.RoleLanguageFeature` instead.
    """

    def resolve_link(
        self, context: DocumentLinkContext, name: str, domain: Optional[str], label: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return a link corresponding to the given target.

        Parameters
        ----------
        context
           The document link context

        domain
           The name (if applicable) of the domain the role is a member of

        name
           The name of the role to generate completion suggestions for.

        label
           The label of the target to provide the link for
        """


class Roles(LanguageFeature):
    """Role support for the language server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._documentation: Dict[str, Dict[str, str]] = {}
        """Cache for documentation."""

        self._features: Dict[str, RoleLanguageFeature] = {}
        """Collection of registered features"""

    def add_feature(self, feature: RoleLanguageFeature):
        """Register a role language feature

        Parameters
        ----------
        feature
           The role language feature
        """
        key = f"{feature.__module__}.{feature.__class__.__name__}"

        # Create a unique key for this instance.
        if key in self._features:
            key += f".{len([k for k in self._features.keys() if k.startswith(key)])}"

        self._features[key] = feature

    def add_target_definition_provider(self, provider: TargetDefinition) -> None:
        """Register a :class:`~esbonio.lsp.roles.TargetDefinition` provider.

        .. deprecated:: 0.15.0

           This will be removed in ``v1.0`` use
           :meth:`~esbonio.lsp.roles.Roles.add_feature` with a
           :class:`~esbonio.lsp.roles.RoleLanguageFeature` subclass instead.

        Parameters
        ----------
        provider
           The provider to register
        """

        warnings.warn(
            "TargetDefinition providers are deprecated in favour of "
            "RoleLanguageFeatures, this method will be removed in v1.0",
            DeprecationWarning,
            stacklevel=2,
        )

        name = provider.__class__.__name__
        key = f"{provider.__module__}.{name}.definition"

        def find_target_definitions(self, context, name, domain, label):
            return provider.find_definitions(context, name, domain)

        feature = type(
            f"{name}TargetDefinitionProvider",
            (RoleLanguageFeature,),
            {"find_target_definitions": find_target_definitions},
        )()

        self._features[key] = feature

    def add_target_link_provider(self, provider: TargetLink) -> None:
        """Register a :class:`~esbonio.lsp.roles.TargetLink` provider.

        .. deprecated:: 0.15.0

           This will be removed in ``v1.0`` use
           :meth:`~esbonio.lsp.roles.Roles.add_feature` with a
           :class:`~esbonio.lsp.roles.RoleLanguageFeature` subclass instead.

        Parameters
        ----------
        provider
           The provider to register
        """

        warnings.warn(
            "TargetLink providers are deprecated in favour of "
            "RoleLanguageFeatures, this method will be removed in v1.0",
            DeprecationWarning,
            stacklevel=2,
        )

        name = provider.__class__.__name__
        key = f"{provider.__module__}.{name}.link"

        feature = type(
            f"{name}TargetLinkProvider",
            (RoleLanguageFeature,),
            {"resolve_target_link": provider.resolve_link},
        )()

        self._features[key] = feature

    def add_target_completion_provider(self, provider: TargetCompletion) -> None:
        """Register a :class:`~esbonio.lsp.roles.TargetCompletion` provider.

        .. deprecated:: 0.15.0

           This will be removed in ``v1.0`` use
           :meth:`~esbonio.lsp.roles.Roles.add_feature` with a
           :class:`~esbonio.lsp.roles.RoleLanguageFeature` subclass instead.

        Parameters
        ----------
        provider
           The provider to register
        """

        warnings.warn(
            "TargetCompletion providers are deprecated in favour of "
            "RoleLanguageFeatures, this method will be removed in v1.0",
            DeprecationWarning,
            stacklevel=2,
        )

        name = provider.__class__.__name__
        key = f"{provider.__module__}.{name}.completion"

        feature = type(
            f"{name}TargetCompletionProvider",
            (RoleLanguageFeature,),
            {"complete_targets": provider.complete_targets},
        )()

        self._features[key] = feature

    def add_documentation(self, documentation: Dict[str, Dict[str, Any]]) -> None:
        """Register role documentation.

        ``documentation`` should be a dictionary of the form ::

           documentation = {
               "raw(docutils.parsers.rst.roles.raw_role)": {
                   "is_markdown": true,
                   "license": "https://...",
                   "source": "https://...",
                   "description": [
                       "# :raw:",
                       "The raw role is used for...",
                       ...
                   ]
               }
           }

        where the key is of the form `name(dotted_name)`. There are cases where a role's
        implementation is not sufficient to uniquely identify it as multiple roles can
        be provided by a single class.

        This means the key has to be a combination of the ``name`` the user writes in
        an reStructuredText document and ``dotted_name`` is the fully qualified name of
        the role's implementation.

        .. note::

           If there is a clash with an existing key, the existing value will be
           overwritten with the new value.

        The values in this dictionary are themselves dictionaries with the following
        fields.

        ``description``
           A list of strings for the role's usage.

        ``is_markdown``
           A boolean flag used to indicate whether the ``description`` is written in
           plain text or markdown.

        ``source``
           The url to the documentation's source.

        ``license``
           The url to the documentation's license.

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

    completion_triggers = [ROLE, DEFAULT_ROLE]
    definition_triggers = [ROLE]
    hover_triggers = [ROLE]
    implementation_triggers = [ROLE]

    def definition(self, context: DefinitionContext) -> List[Location]:

        domain = context.match.group("domain") or ""
        name = context.match.group("name")
        label = context.match.group("label")

        # Be sure to only match complete roles
        if not label or not context.match.group(0).endswith("`"):
            return []

        return self.find_target_definitions(context, name, domain, label)

    def find_target_definitions(
        self, context: DefinitionContext, name: str, domain: str, label: str
    ) -> List[Location]:

        definitions = []

        for feature_name, feature in self._features.items():
            try:
                definitions += feature.find_target_definitions(
                    context, name, domain, label
                )
            except Exception:
                self.logger.error(
                    "Unable to find definitions of '%s' for role ':%s:', "
                    "error in feature: '%s'",
                    label,
                    f"{domain}:{name}" if domain else name,
                    feature_name,
                    exc_info=True,
                )

        return definitions

    def document_link(self, context: DocumentLinkContext) -> List[DocumentLink]:

        links = []

        for line, text in enumerate(context.doc.lines):
            for match in ROLE.finditer(text):
                label = match.group("label")

                # Be sure to only match complete roles
                if not label or not match.group(0).endswith("`"):
                    continue

                domain = match.group("domain")
                name = match.group("name")

                target, tooltip = self.resolve_target_link(context, name, domain, label)
                if not target:
                    continue

                idx = match.group(0).index(label)
                start = match.start() + idx
                end = start + len(label)

                link = DocumentLink(
                    target=target,
                    tooltip=tooltip if context.tooltip_support else None,
                    range=Range(
                        start=Position(line=line, character=start),
                        end=Position(line=line, character=end),
                    ),
                )

                links.append(link)

        return links

    def resolve_target_link(
        self, context: DocumentLinkContext, name: str, domain: str, label: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Resolve a given document link."""

        for feature_name, feature in self._features.items():
            try:
                target, tooltip = feature.resolve_target_link(
                    context, name, domain, label
                )

                if target:
                    return target, tooltip
            except Exception:
                self.logger.error(
                    "Unable to resolve target link '%s' for role ':%s:', "
                    "error in feature: '%s'",
                    label,
                    f"{domain}:{name}" if domain else name,
                    feature_name,
                    exc_info=True,
                )

        return None, None

    def complete(self, context: CompletionContext) -> List[CompletionItem]:
        """Generate completion suggestions relevant to the current context.

        This function is a little intense, but its sole purpose is to determine the
        context in which the completion request is being made and either return
        nothing, or the results of :meth:`~esbonio.lsp.roles.Roles.complete_roles` or
        :meth:`esbonio.lsp.roles.Roles.complete_targets` whichever is appropriate.

        Parameters
        ----------
        context:
           The context of the completion request.
        """

        # Do not suggest completions within the middle of Python code.
        if context.location == "py":
            return []

        groups = context.match.groupdict()
        target = groups["target"]

        # All text matched by the regex
        text = context.match.group(0)
        start, end = context.match.span()

        if target:
            target_index = start + text.find(target)

            # Only trigger target completions if the request was made from within
            # the target part of the role.
            if target_index <= context.position.character <= end:
                return self.complete_targets(context)

        # If there's no indent, then this can only be a role definition
        indent = context.match.group(1)
        if indent == "":
            return self.complete_roles(context)

        # Otherwise, search backwards until we find a blank line or an unindent
        # so that we can determine the appropriate context.
        linum = context.position.line - 1

        try:
            line = context.doc.lines[linum]
        except IndexError:
            return self.complete_roles(context)

        while linum >= 0 and line.startswith(indent):
            linum -= 1
            line = context.doc.lines[linum]

        # Unless we are within a directive's options block, we should offer role
        # suggestions
        if DIRECTIVE.match(line):
            return []

        return self.complete_roles(context)

    def completion_resolve(self, item: CompletionItem) -> CompletionItem:

        # We need extra info to know who to call
        if not item.data:
            return item

        data = typing.cast(Dict, item.data)
        ctype = data.get("completion_type", "")

        if ctype == "role":
            return self.completion_resolve_role(item)

        return item

    def suggest_roles(self, context: CompletionContext) -> Iterable[Tuple[str, Any]]:
        """Suggest roles that may be used, given a completion context.

        Parameters
        ----------
        context
           The completion context
        """
        for name, feature in self._features.items():
            try:
                yield from feature.suggest_roles(context)
            except Exception:
                self.logger.error(
                    "Unable to suggest roles, error in feature: '%s'",
                    name,
                    exc_info=True,
                )

    def complete_roles(self, context: CompletionContext) -> List[CompletionItem]:

        match = context.match
        groups = match.groupdict()
        domain = groups["domain"] or ""
        items = []

        # Insert text starting from the starting ':' character of the role.
        start = match.span()[0] + match.group(0).find(":")
        end = start + len(groups["role"])

        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )

        for name, role in self.suggest_roles(context):

            if not name.startswith(domain):
                continue

            try:
                dotted_name = f"{role.__module__}.{role.__name__}"
            except AttributeError:
                dotted_name = f"{role.__module__}.{role.__class__.__name__}"

            insert_text = f":{name}:"
            item = CompletionItem(
                label=name,
                kind=CompletionItemKind.Function,
                detail=f"{dotted_name}",
                filter_text=insert_text,
                text_edit=TextEdit(range=range_, new_text=insert_text),
                data={"completion_type": "role"},
            )

            items.append(item)

        return items

    def completion_resolve_role(self, item: CompletionItem) -> CompletionItem:

        # We need the detail field set to the role implementation's fully qualified name
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

    def suggest_targets(
        self, context: CompletionContext, name: str, domain: str
    ) -> List[CompletionItem]:

        targets = []

        for feature_name, feature in self._features.items():
            try:
                targets += feature.complete_targets(context, name, domain)
            except Exception:
                self.logger.error(
                    "Unable to suggest targets for role ':%s:', error in feature: '%s'",
                    f"{domain}:{name}" if domain else name,
                    feature_name,
                    exc_info=True,
                )

        return targets

    def complete_targets(self, context: CompletionContext) -> List[CompletionItem]:
        """Generate the list of role target completion suggestions."""

        groups = context.match.groupdict()

        # Handle the default role case.
        if "role" not in groups:
            domain, name = self.rst.get_default_role()
            if not name:
                return []
        else:
            name = groups["name"]
            domain = groups["domain"]

        domain = domain or ""
        name = name or ""

        # Only generate suggestions for "aliased" targets if the request comes from
        # within the <> chars.
        if groups["alias"]:
            text = context.match.group(0)
            start = context.match.span()[0] + text.find(groups["alias"])
            end = start + len(groups["alias"])

            if start <= context.position.character <= end:
                return []

        targets = []

        startchar = "<" if "<" in groups["target"] else "`"
        endchars = ">`" if "<" in groups["target"] else "`"

        start, end = context.match.span()
        start += context.match.group(0).index(startchar) + 1
        range_ = Range(
            start=Position(line=context.position.line, character=start),
            end=Position(line=context.position.line, character=end),
        )
        prefix = context.match.group(0)[start:]
        modifier = groups["modifier"] or ""

        for candidate in self.suggest_targets(context, name, domain):

            # Don't interfere with items that already carry a `text_edit`, allowing
            # some providers (like filepaths) to do something special.
            if not candidate.text_edit:
                new_text = candidate.insert_text or candidate.label

                # This is rather annoying, but `filter_text` needs to start with
                # the text we are going to replace, otherwise VSCode won't show our
                # suggestions!
                candidate.filter_text = f"{prefix}{new_text}"

                candidate.text_edit = TextEdit(
                    range=range_, new_text=f"{modifier}{new_text}"
                )
                candidate.insert_text = None

            if not candidate.text_edit.new_text.endswith(endchars):
                candidate.text_edit.new_text += endchars

            targets.append(candidate)

        return targets

    def hover(self, context: HoverContext) -> str:

        if context.location not in {"rst", "docstring"}:
            return ""

        name = context.match.group("name")
        domain = context.match.group("domain")

        # Determine if the hover is on the :role: itself, or within the `target`.
        idx = context.position.character - context.match.start()
        prefix = context.match.group(0)[:idx]

        if "`" in prefix:
            return self.hover_target(context, name, domain)

        return self.hover_role(context, name, domain)

    def hover_role(self, context: HoverContext, name: str, domain: str) -> str:

        label = f"{domain}:{name}" if domain else name
        role = self.get_implementation(name, domain)
        if not role:
            return ""

        try:
            dotted_name = f"{role.__module__}.{role.__name__}"
        except AttributeError:
            dotted_name = f"{role.__module__}.{role.__class__.__name__}"

        documentation = self.get_documentation(label, dotted_name)
        if not documentation:
            return ""

        return documentation.get("description", "")

    def hover_target(
        self, context: HoverContext, name: str, domain: Optional[str]
    ) -> str:
        # TODO: Add extension point for providers to contribute hovers for a target.
        return ""

    def get_roles(self) -> Dict[str, Any]:
        """Return a dictionary of all known roles."""

        roles = {}

        for name, feature in self._features.items():
            self.logger.debug("calling '%s'", name)
            try:
                roles.update(feature.index_roles())
            except Exception:
                self.logger.error(
                    "Unable to index roles, error in feature '%s'", name, exc_info=True
                )

        return roles

    def get_implementation(self, role: str, domain: str) -> Optional[Any]:
        """Return the implementation of a role given its name

        Parameters
        ----------
        role
           The name of the role.

        domain
           The domain of the role, if applicable.
        """

        if domain:
            name = f"{domain}:{role}"
        else:
            name = role

        for feature_name, feature in self._features.items():
            try:
                impl = feature.get_implementation(role, domain)
                if impl is not None:
                    return impl
            except Exception:
                self.logger.error(
                    "Unable to get implementation for ':%s:', error in feature: '%s'\n%s",
                    name,
                    feature_name,
                    exc_info=True,
                )

        self.logger.debug("Unable to get implementation for ':%s:', unknown role", name)
        return None

    def implementation(self, context: ImplementationContext) -> List[Location]:

        region = context.match.group("role")
        name = context.match.group("name")
        domain = context.match.group("domain")

        start = context.match.start() + context.match.group(0).index(region)
        end = start + len(region)

        self.logger.debug("%s, %s, %s", region, name, domain)
        self.logger.debug("%s, %s", start, end)

        if start <= context.position.character <= end:
            return self.find_role_implementation(context, name, domain)

        return []

    def find_role_implementation(
        self, context: ImplementationContext, name: str, domain: str
    ) -> List[Location]:

        impl = self.get_implementation(name, domain)
        if impl is None:
            return []

        location = get_object_location(impl, self.logger)
        if location is not None:
            return [location]

        # Some roles are implemented as instances of some class
        location = get_object_location(impl.__class__, self.logger)
        if location is not None:
            return [location]

        return []

    def get_documentation(
        self, label: str, implementation: str
    ) -> Optional[Dict[str, Any]]:
        """Return the documentation for the given role, if available.

        If documentation for the given ``label`` cannot be found, this function will also
        look for the label under the project's :confval:`sphinx:primary_domain` followed
        by the ``std`` domain.

        Parameters
        ----------
        label:
           The name of the role, as the user would type in an reStructuredText file.
        implementation:
           The full dotted name of the role's implementation.
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
    rst.add_feature(Roles(rst))
