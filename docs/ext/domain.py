from __future__ import annotations

import typing

from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain
from sphinx.domains import ObjType
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_id
from sphinx.util.nodes import make_refnode

if typing.TYPE_CHECKING:
    from typing import Dict
    from typing import Optional
    from typing import Tuple

    from docutils.nodes import Element
    from sphinx.addnodes import pending_xref
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import OptionSpec


def config_scope(argument: str):
    """Directive option parser for configuration scopes"""
    return directives.choice(argument, ("global", "project"))


def config_type(argument: str):
    """Directive option parser for configuration value types"""
    types_ = {"string", "integer", "boolean", "string[]", "object"}
    return directives.choice(argument, types_)


class ConfigValue(ObjectDescription[str]):
    """Description of a configuration value."""

    option_spec: OptionSpec = {
        "scope": config_scope,
        "type": config_type,
    }

    def handle_signature(self, sig: str, signode: addnodes.desc_signature) -> str:
        scope = self.options.get("scope", "global")
        type_ = self.options.get("type", "string")

        # Prefix the configuration option, denoting its type and configuration scope.
        signode += addnodes.desc_annotation(
            scope,
            "",
            addnodes.desc_sig_literal_string("", scope),
            addnodes.desc_sig_space(),
            addnodes.desc_sig_keyword_type("", type_),
            addnodes.desc_sig_space(),
        )
        signode += addnodes.desc_name(sig, sig)
        return sig

    def add_target_and_index(
        self, name: str, sig: str, signode: addnodes.desc_signature
    ) -> None:
        node_id = make_id(self.env, self.state.document, term=name)
        signode["ids"].append(node_id)

        domain: EsbonioDomain = self.env.domains["esbonio"]
        domain.config_values[name] = (self.env.docname, node_id)


class EsbonioDomain(Domain):
    """A domain dedicated to documenting the esbonio language server"""

    name = "esbonio"
    label = "Esbonio"

    object_types: Dict[str, ObjType] = {
        "config": ObjType("config", "conf"),
    }

    directives = {
        "config": ConfigValue,
    }

    roles = {
        "conf": XRefRole(),
    }

    initial_data = {
        "config_values": {},
    }

    @property
    def config_values(self) -> dict[str, Tuple[str, str]]:
        return self.data.setdefault("config_values", {})

    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        type: str,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> Optional[Element]:
        """Resolve cross references"""

        if (entry := self.config_values.get(target, None)) is None:
            return None

        return make_refnode(
            builder, fromdocname, entry[0], entry[1], [contnode], target
        )


def setup(app: Sphinx):
    app.add_domain(EsbonioDomain)
