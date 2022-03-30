API Reference
=============

.. warning::

   While we will try not to break the API outlined below, until the language server
   reaches ``v1.0`` we do not offer any stability guarantees.

Language Servers
----------------

.. autofunction:: esbonio.lsp.create_language_server

.. autoclass:: esbonio.lsp.rst.RstLanguageServer
   :members:
   :show-inheritance:

.. autoclass:: esbonio.lsp.sphinx.SphinxLanguageServer
   :members:
   :show-inheritance:

Language Features
-----------------

.. autoclass:: esbonio.lsp.rst.LanguageFeature
   :members:

.. autoclass:: esbonio.lsp.rst.CompletionContext
   :members:

.. autoclass:: esbonio.lsp.rst.DefinitionContext
   :members:

Directives
^^^^^^^^^^

.. currentmodule:: esbonio.lsp.directives

.. autodata:: DIRECTIVE
   :annotation: = re.compile(...)

.. autodata:: DIRECTIVE_OPTION
   :annotation: = re.compile(...)

.. autoclass:: ArgumentCompletion
   :members:

.. autoclass:: Directives
   :members: add_argument_completion_provider, add_documentation

Roles
^^^^^

.. currentmodule:: esbonio.lsp.roles

.. autodata:: ROLE
   :annotation: = re.compile(...)

.. autodata:: DEFAULT_ROLE
   :annotation: = re.compile(...)

.. autoclass:: Roles
   :members: add_documentation, add_target_definition_provider, add_target_completion_provider

.. autoclass:: TargetCompletion
   :members:

.. autoclass:: TargetDefinition
   :members:

Testing
-------

.. automodule:: esbonio.lsp.testing
   :members:
