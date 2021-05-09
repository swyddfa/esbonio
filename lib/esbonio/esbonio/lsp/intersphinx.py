"""Intersphinx support."""
import re

from typing import List, Optional
from pygls.lsp.types import (
    CompletionItem,
    CompletionItemKind,
    Position,
)
from pygls.workspace import Document

import esbonio.lsp as lsp
from esbonio.lsp.roles import (
    COMPLETION_TARGETS,
    DEFAULT_TARGET,
    PARTIAL_PLAIN_TARGET,
    PARTIAL_ALIASED_TARGET,
)
from esbonio.lsp.sphinx import get_domains


PARTIAL_INTER_PLAIN_TARGET = re.compile(
    r"""
    (^|.*[ ])               # roles must be preceeded by a space, or start the line
    (?P<role>:              # roles start with the ':' character
    (?!:)                   # make sure the next character is not ':'
    (?P<domain>[\w]+:)?     # there may be a domain namespace
    (?P<name>[\w-]*)        # followed by the role name
    :)                      # the role name ends with a ':'
    `                       # the target begins with a '`'
    (?P<project>[^<:`]*)    # match "plain link" targets
    :                       # projects end with a ':'
    $
    """,
    re.MULTILINE | re.VERBOSE,
)
"""A regular expression that matches a partial "plain" intersphinx target.

For example::

   :ref:`python:som

Used when generating auto complete suggestions.
"""

PARTIAL_INTER_ALIASED_TARGET = re.compile(
    r"""
    (^|.*[ ])            # roles must be preceeded by a space, or start the line
    (?P<role>:           # roles start with the ':' character
    (?!:)                # make sure the next character is not ':'
    (?P<domain>[\w]+:)?  # there may be a domain namespace
    (?P<name>[\w-]*)     # followed by the role name
    :)                   # the role name ends with a ':'
    `                    # the target begins with a '`'`
    .*<                  # the actual target name starts after a '<'
    (?P<project>[^`:]*)  # match "aliased" targets
    :                    # projects end with a ':'
    $
    """,
    re.MULTILINE | re.VERBOSE,
)
"""A regular expression that matches a partial "aliased" intersphinx target.

For example::

   :ref:`More Info<python:som

Used when generating auto complete suggestions.
"""


class InterSphinx(lsp.LanguageFeature):
    """Intersphinx support for the language server."""

    def initialized(self, config: lsp.SphinxConfig):

        self.targets = {}
        self.target_types = {}
        self.projects = {}

        if self.rst.app and hasattr(self.rst.app.env, "intersphinx_named_inventory"):
            self.discover_inventories()

    def discover_inventories(self):
        """Look up intersphinx inventories to offer as autocomplete suggestions.

        *This method only needs to be called once per application instance.*

        Assuming that the application has the ``intersphinx`` extension enabled and
        configured, this will look for the ``intersphinx_named_inventory`` attribute
        on the Sphinx application's build environment and index each of the availble
        projects.

        This will also loop through each domain object and construct the
        ``target_types`` dictionary - very similar to
        :meth:`~esbonio.lsp.roles.Roles.discover_roles` on the ``Roles`` feature, except
        that intersphinx always uses a domain's namespace even if ``primary_domain`` is
        set in the app's config.

        Finally, as target completions for other projects aren't going to change over
        the course of an editing session, it's also safe to index them once on init.
        """

        inv = self.rst.app.env.intersphinx_named_inventory
        self.projects = {v: self.project_to_completion_item(v) for v in inv.keys()}

        for _, domain in get_domains(self.rst.app):

            # Intersphinx entries are always namespaced, regardless of the
            # `primary_domain` setting.
            fmt = "{domain.name}:{name}"

            # Build a map we can use to lookup target completions
            for name, item_type in domain.object_types.items():
                for role in item_type.roles:
                    key = fmt.format(name=role, domain=domain)
                    target_types = self.target_types.get(key, None)

                    if target_types is None:
                        target_types = []

                    target_types.append(fmt.format(name=name, domain=domain))
                    self.target_types[key] = target_types

            # Index each of the completion targets.
            for project, types in inv.items():
                project_map = {}

                for target_type, targets in types.items():
                    target_type_map = {}

                    for label, target in targets.items():
                        target_type_map[label] = self.target_to_completion_item(
                            label, target, target_type
                        )

                    project_map[target_type] = target_type_map

                self.targets[project] = project_map

        self.logger.info("Discovered %s intersphinx projects", len(self.projects))
        self.logger.debug("Projects: %s", self.projects.keys())

        self.logger.info("Discovered %s target types", len(self.target_types))
        self.logger.debug("Target types: %s", self.target_types)

    suggest_triggers = [
        PARTIAL_PLAIN_TARGET,
        PARTIAL_ALIASED_TARGET,
        PARTIAL_INTER_PLAIN_TARGET,
        PARTIAL_INTER_ALIASED_TARGET,
    ]

    def suggest(
        self, match: "re.Match", doc: Document, position: Position
    ) -> List[CompletionItem]:

        # As a unfortunate consequence of naming choices, we're in the counter intuitive
        # situation where
        #
        # - A match containing a "target" regex group should suggest project names
        # - A match containing a "project" regex group should suggest targets
        groups = match.groupdict()

        if "target" in groups:
            return self.suggest_projects(match)

        return self.suggest_targets(match)

    def suggest_projects(self, match: "re.Match") -> List[CompletionItem]:

        if self.get_target_types(match):
            self.logger.info("Suggesting projects")
            return list(self.projects.values())

        return []

    def suggest_targets(self, match: "re.Match") -> List[CompletionItem]:
        # TODO: Detect if we're in an angle bracket e.g. :ref:`More Info <python:`
        # and add the closing '>' to the completion item insert text.
        self.logger.info("Suggesting targets")

        target_types = self.get_target_types(match)
        if target_types is None:
            return []

        project = self.targets.get(match.group("project"), None)
        if project is None:
            return []

        targets = []
        for target_type in target_types:
            items = project.get(target_type, {})
            targets += items.values()

        return targets

    def get_target_types(self, match: "re.Match") -> Optional[List[str]]:
        """Returns the list of target types that are targeted by the role we're
        generating suggestions for."""

        role = match.group("name")
        domain = match.group("domain") or ""
        primary_domain = self.rst.app.config.primary_domain or ""

        self.logger.debug("Looking up target types for '%s%s'", domain, role)

        # Attempt to find the right key..
        for key in [f"{domain}{role}", f"{primary_domain}:{role}", f"std:{role}"]:
            target_types = self.target_types.get(key, None)
            self.logger.debug("Targets types for '%s': %s", key, target_types)

            if target_types is not None:
                return target_types

    def project_to_completion_item(self, project: str) -> CompletionItem:
        return CompletionItem(
            label=project, detail="intersphinx", kind=CompletionItemKind.Module
        )

    def target_to_completion_item(
        self, label: str, target, target_type: str
    ) -> CompletionItem:

        key = target_type

        if ":" in key:
            key = ":".join(key.split(":")[1:])

        completion_type = COMPLETION_TARGETS.get(key, DEFAULT_TARGET)
        source, version, _, display = target

        if display == "-":
            display = label

        if version:
            version = f" v{version}"

        detail = f"{display} - {source}{version}"

        return CompletionItem(
            label=label, kind=completion_type.kind, detail=detail, insert_text=label
        )


def setup(rst: lsp.RstLanguageServer):
    intersphinx = InterSphinx(rst)
    rst.add_feature(intersphinx)
