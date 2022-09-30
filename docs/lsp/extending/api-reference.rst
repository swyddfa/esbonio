API Reference
=============

.. warning::

   While we will try not to break the API outlined below, until the language server
   reaches ``v1.0`` we do not offer any stability guarantees.

Language Servers
----------------

.. autofunction:: esbonio.lsp.create_language_server

RstLanguageServer
^^^^^^^^^^^^^^^^^

.. autoclass:: esbonio.lsp.rst.RstLanguageServer
   :members:
   :show-inheritance:

.. autoclass:: esbonio.lsp.rst.InitializationOptions
   :members:

.. autoclass:: esbonio.lsp.rst.ServerConfig
   :members:


SphinxLanguageServer
^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: esbonio.lsp.sphinx

.. autoclass:: SphinxLanguageServer
   :members:
   :show-inheritance:

.. autoclass:: InitializationOptions
   :members:

.. autoclass:: SphinxServerConfig
   :members:

.. autoclass:: SphinxConfig
   :members:

.. autoclass:: MissingConfigError

Language Features
-----------------

.. autoclass:: esbonio.lsp.LanguageFeature
   :members:

.. autoclass:: esbonio.lsp.CompletionContext
   :members:

.. autoclass:: esbonio.lsp.DefinitionContext
   :members:

.. autoclass:: esbonio.lsp.DocumentLinkContext
   :members:


Roles
^^^^^

.. currentmodule:: esbonio.lsp.roles

.. autodata:: ROLE
   :annotation: = re.compile(...)

.. autodata:: DEFAULT_ROLE
   :annotation: = re.compile(...)

.. autoclass:: Roles
   :members: add_documentation, add_target_definition_provider, add_target_completion_provider, add_target_link_provider

.. autoclass:: TargetCompletion
   :members:

.. autoclass:: TargetDefinition
   :members:

.. autoclass:: TargetLink
   :members:

Testing
-------

.. automodule:: esbonio.lsp.testing
   :members:
