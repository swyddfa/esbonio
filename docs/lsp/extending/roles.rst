Roles
=====

How To Guides
-------------

The following guides outlne how to extens the language server to add support for your custom roles.

.. toctree::
   :glob:
   :maxdepth: 1

   roles/*

API Reference
-------------

.. currentmodule:: esbonio.lsp.roles

.. autoclass:: Roles
   :members: add_documentation,
             add_feature,
             add_target_completion_provider,
             add_target_definition_provider,
             add_target_link_provider,
             get_documentation,
             get_implementation,
             get_roles,
             resolve_target_link,
             suggest_roles,
             suggest_targets

.. autoclass:: RoleLanguageFeature
   :members:

.. autodata:: esbonio.lsp.util.patterns.ROLE
   :no-value:

.. autodata:: esbonio.lsp.util.patterns.DEFAULT_ROLE
   :no-value:

.. autoclass:: TargetDefinition
   :members:

.. autoclass:: TargetCompletion
   :members:

.. autoclass:: TargetLink
   :members:
