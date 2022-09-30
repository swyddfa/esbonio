Directives
==========

How To Guides
-------------

The following guides outline how to extend the language server to add support for your custom directives.

.. toctree::
   :glob:
   :maxdepth: 1

   directives/*

API Reference
-------------

.. currentmodule:: esbonio.lsp.directives

.. autoclass:: Directives
   :members: add_argument_completion_provider,
             add_argument_definition_provider,
             add_argument_link_provider,
             add_documentation,
             add_feature,
             get_directives,
             get_implementation,
             suggest_directives,
             suggest_options

.. autoclass:: DirectiveLanguageFeature
   :members:

.. autodata:: esbonio.lsp.util.patterns.DIRECTIVE
   :no-value:

.. autodata:: esbonio.lsp.util.patterns.DIRECTIVE_OPTION
   :no-value:

.. autoclass:: ArgumentCompletion
   :members:

.. autoclass:: ArgumentDefinition
   :members:

.. autoclass:: ArgumentLink
   :members:
