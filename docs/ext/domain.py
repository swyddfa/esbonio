from typing import Dict

from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain
from sphinx.domains import ObjType
from sphinx.roles import XRefRole
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


def setup(app: Sphinx):
    app.add_domain(EsbonioDomain)
