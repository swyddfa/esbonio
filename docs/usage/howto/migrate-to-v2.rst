.. _lsp-v2-migration:

How To Migrate to v2
====================

This guide covers the breaking changes between the ``v1.x`` and ``v2.x`` versions of the language server and how to adapt to them.

Sphinx v6 No Longer Supported
-----------------------------

Inline with the :ref:`about-versioning` policy, while Esbonio ``v2.x`` adds support for Sphinx v9, support for Sphinx v6 has been removed.

Configuration Changes
---------------------

The default values for the following configuration options have been changed.

- :esbonio:conf:`esbonio.logging.level` now defaults to ``info``
- :esbonio:conf:`esbonio.logging.format` now defaults to ``[%(method)s(%(msgid)s)][%(name)s] %(message)s``
- :esbonio:conf:`esbonio.server.completion.preferredInsertBehavior` now defaults to ``insert``

Logging Changes
---------------

When turned up to ``debug``, esbonio's log output can become *very* verbose.

Unfortunately, this doesn't necessarily mean that diagnosing issues with the server is easy, especially if you're not famaliar with the server's internals.
This is despite the fact the server already provides a rich set of logging options (see :esbonio:conf:`esbonio.logging.config`), allowing you to tailor the output from specific components of the server.

The issue is that this flexibility was along the wrong axis, requiring you to be familiar with the internal architecture of the server in order to decide which components to pay attention to.

This release attempts to rectify this by introducing a series of changes to the logging system.
Consider the following output from a ``v1.x`` version of the server:

.. raw:: html

   <style>
   .limit-height div.highlight pre {
      max-height: 300px;
      overflow: auto;
   }
   </style>

.. code-block:: none
   :class: limit-height

   [esbonio.Configuration] ConfigurationContext(file_scope='', workspace_scope='')
   [esbonio.Configuration] esbonio.server.completion: {
   "preferredInsertBehavior": "replace"
   }
   [esbonio.Configuration] CompletionConfig(preferred_insert_behavior='replace')
   [esbonio.Configuration] Previous: None
   [esbonio.Configuration] Current: CompletionConfig(preferred_insert_behavior='replace')
   [esbonio.Configuration] ConfigChangeEvent(scope='', value=CompletionConfig(preferred_insert_behavior='replace'), previous=None)
   [esbonio] Task finished: <Task finished name='Task-23' coro=<PreviewManager.show_preview_uri() done, defined at /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/server/features/preview_manager/__init__.py:187> result=None>
   [esbonio.ProjectManager] No applicable project for uri: file:///workspaces/develop/docs/usage/howto/migrate-to-v2.rst
   Running Sphinx v9.1.0
   loading translations [en]... done
   The configuration has changed (2 options: 'html_static_path', 'pygments_dark_style')
   loading pickled environment... done
   myst v5.0.0: MdParserConfig(commonmark_only=False, gfm_only=False, enable_extensions=set(), disable_syntax=[], all_links_external=False, links_external_new_tab=False, url_schemes=('http', 'https', 'mailto', 'ftp'), ref_domains=None, fence_as_directive=set(), number_code_blocks=[], title_to_header=False, heading_anchors=0, heading_slug_func=None, html_meta={}, footnote_sort=True, footnote_transition=True, words_per_minute=200, substitutions={}, linkify_fuzzy_links=True, dmath_allow_labels=True, dmath_allow_space=True, dmath_allow_digits=True, dmath_double_inline=False, update_mathjax=True, mathjax_classes='tex2jax_process|mathjax_process|math|output_area', enable_checkboxes=False, suppress_warnings=[], highlight_code_blocks=True)
   /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/sphinx_agent/handlers/domains.py:281: RemovedInSphinx10Warning: The iter() interface for _InventoryItem objects is deprecated. Please access the `project_name`, `project_version`, `uri`, and `displayname` attributes directly.
   (name, version, _, _) = next(iter(next(iter(project.values())).values()))
   /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/sphinx_agent/handlers/domains.py:303: RemovedInSphinx10Warning: The iter() interface for _InventoryItem objects is deprecated. Please access the `project_name`, `project_version`, `uri`, and `displayname` attributes directly.
   for objname, (_, _, item_uri, display) in items.items():
   [esbonio.SphinxManager] SphinxClient[0f684895-d015-46f9-ac3b-623c654a720b]: ClientState.Starting -> ClientState.Running
   [esbonio.ProjectManager] Registered project for scope 'file:///workspaces/develop/docs': '/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml/esbonio.db'
   [client] sphinx/appCreated: {
   "version": "9.1.0",
   "python": "3.14.3",
   "conf_dir": "/workspaces/develop/docs",
   "build_dir": "/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml",
   "builder_name": "dirhtml",
   "src_dir": "/workspaces/develop/docs",
   "dbpath": "/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml/esbonio.db"
   }
   [esbonio] Task finished: <Task finished name='Task-17' coro=<SphinxManager._create_or_replace_client() done, defined at /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/server/features/sphinx_manager/manager.py:316> result=None>
   [esbonio.PreviewManager] Previewing file: 'file:///workspaces/develop/docs/usage/reference/configuration.rst'
   [esbonio] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst>
   [esbonio.DirectiveFeature] Resolving argument link for directive: 'highlight' (sphinx.directives.code.Highlight)
   [esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-completion ['std:label'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-developer ['std:label'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-logging ['std:label'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-sphinx ['std:label'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-preview ['std:label'] None
   [esbonio.RolesFeature] Unknown role 'external:ref'
   [esbonio.RolesFeature] Unknown role 'external:ref'
   [esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.level ['esbonio:config'] None
   [esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.format ['esbonio:config'] None
   [esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.filepath ['esbonio:config'] None
   [esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.stderr ['esbonio:config'] None
   [esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.window ['esbonio:config'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configure-sphinx-build-cmd ['std:label'] None
   [esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.sphinx.buildArguments ['esbonio:config'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:option' (sphinx.domains.std.OptionXRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> sphinx:sphinx-build.-D ['std:cmdoption'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:option' (sphinx.domains.std.OptionXRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> sphinx:sphinx-build.-A ['std:cmdoption'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configure-sphinx-build-cmd ['std:label'] None
   [esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configure-sphinx-build-env ['std:label'] None
   [esbonio.PreviewManager] Preview available at: http://localhost:40535/usage/reference/configuration/?ws=ws%3A%2F%2Flocalhost%3A43647
   [esbonio.PreviewManager] window/showDocument: ShowDocumentResult(success=True)

There is a *lot* going on here, and if you're trying to debug issues with your Sphinx setup, most of it is irrelevant!

In esbonio ``v2.x`` log messages will be prefixed with the LSP method they are associated with, as shown in the equivalent ``v2.x`` output below:

.. code-block:: none
   :class: limit-height

   [initialized()][esbonio.Configuration] ConfigurationContext(file_scope='', workspace_scope='')
   [initialized()][esbonio.Configuration] esbonio.server.completion: {
   "preferredInsertBehavior": "replace"
   }
   [initialized()][esbonio.Configuration] CompletionConfig(preferred_insert_behavior='replace')
   [initialized()][esbonio.Configuration] Previous: None
   [initialized()][esbonio.Configuration] Current: CompletionConfig(preferred_insert_behavior='replace')
   [initialized()][esbonio.Configuration] ConfigChangeEvent(scope='', value=CompletionConfig(preferred_insert_behavior='replace'), previous=None)
   [initialized()][esbonio] Task finished: <Task finished name='Task-23' coro=<PreviewManager.show_preview_uri() done, defined at /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/server/features/preview_manager/__init__.py:187> result=None>
   [textDocument/documentSymbol(8)][esbonio.ProjectManager] No applicable project for uri: file:///workspaces/develop/docs/usage/howto/migrate-to-v2.rst
   Running Sphinx v9.1.0
   loading translations [en]... done
   The configuration has changed (2 options: 'html_static_path', 'pygments_dark_style')
   loading pickled environment... done
   myst v5.0.0: MdParserConfig(commonmark_only=False, gfm_only=False, enable_extensions=set(), disable_syntax=[], all_links_external=False, links_external_new_tab=False, url_schemes=('http', 'https', 'mailto', 'ftp'), ref_domains=None, fence_as_directive=set(), number_code_blocks=[], title_to_header=False, heading_anchors=0, heading_slug_func=None, html_meta={}, footnote_sort=True, footnote_transition=True, words_per_minute=200, substitutions={}, linkify_fuzzy_links=True, dmath_allow_labels=True, dmath_allow_space=True, dmath_allow_digits=True, dmath_double_inline=False, update_mathjax=True, mathjax_classes='tex2jax_process|mathjax_process|math|output_area', enable_checkboxes=False, suppress_warnings=[], highlight_code_blocks=True)
   /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/sphinx_agent/handlers/domains.py:281: RemovedInSphinx10Warning: The iter() interface for _InventoryItem objects is deprecated. Please access the `project_name`, `project_version`, `uri`, and `displayname` attributes directly.
   (name, version, _, _) = next(iter(next(iter(project.values())).values()))
   /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/sphinx_agent/handlers/domains.py:303: RemovedInSphinx10Warning: The iter() interface for _InventoryItem objects is deprecated. Please access the `project_name`, `project_version`, `uri`, and `displayname` attributes directly.
   for objname, (_, _, item_uri, display) in items.items():
   [initialized()][esbonio.SphinxManager] SphinxClient[0f684895-d015-46f9-ac3b-623c654a720b]: ClientState.Starting -> ClientState.Running
   [initialized()][esbonio.ProjectManager] Registered project for scope 'file:///workspaces/develop/docs': '/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml/esbonio.db'
   [client] sphinx/appCreated: {
   "version": "9.1.0",
   "python": "3.14.3",
   "conf_dir": "/workspaces/develop/docs",
   "build_dir": "/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml",
   "builder_name": "dirhtml",
   "src_dir": "/workspaces/develop/docs",
   "dbpath": "/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml/esbonio.db"
   }
   [initialized()][esbonio] Task finished: <Task finished name='Task-17' coro=<SphinxManager._create_or_replace_client() done, defined at /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/server/features/sphinx_manager/manager.py:316> result=None>
   [workspace/executeCommand(21)][esbonio.PreviewManager] Previewing file: 'file:///workspaces/develop/docs/usage/reference/configuration.rst'
   [textDocument/documentLink(23)][esbonio] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst>
   [textDocument/documentLink(23)][esbonio.DirectiveFeature] Resolving argument link for directive: 'highlight' (sphinx.directives.code.Highlight)
   [textDocument/documentLink(23)][esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [textDocument/documentLink(23)][esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [textDocument/documentLink(23)][esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [textDocument/documentLink(23)][esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [textDocument/documentLink(23)][esbonio.DirectiveFeature] Resolving argument link for directive: 'code-block' (sphinx.directives.code.CodeBlock)
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-completion ['std:label'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-developer ['std:label'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-logging ['std:label'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-sphinx ['std:label'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configuration-preview ['std:label'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Unknown role 'external:ref'
   [textDocument/documentLink(23)][esbonio.RolesFeature] Unknown role 'external:ref'
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.level ['esbonio:config'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.format ['esbonio:config'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.filepath ['esbonio:config'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.stderr ['esbonio:config'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.logging.window ['esbonio:config'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configure-sphinx-build-cmd ['std:label'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'esbonio:conf' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> esbonio.sphinx.buildArguments ['esbonio:config'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:option' (sphinx.domains.std.OptionXRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> sphinx:sphinx-build.-D ['std:cmdoption'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:option' (sphinx.domains.std.OptionXRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> sphinx:sphinx-build.-A ['std:cmdoption'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configure-sphinx-build-cmd ['std:label'] None
   [textDocument/documentLink(23)][esbonio.RolesFeature] Resolving target link for role: 'std:ref' (sphinx.roles.XRefRole)
   [textDocument/documentLink(23)][esbonio.ObjectsProvider] DocumentLinkContext<file:///workspaces/develop/docs/usage/reference/configuration.rst> lsp-configure-sphinx-build-env ['std:label'] None
   [workspace/executeCommand(21)][esbonio.PreviewManager] Preview available at: http://localhost:40535/usage/reference/configuration/?ws=ws%3A%2F%2Flocalhost%3A43647
   [workspace/executeCommand(21)][esbonio.PreviewManager] window/showDocument: ShowDocumentResult(success=True)

Already that should be somewhat easier to parse and you can probably guess that the messages tagged with ``initialized()`` are the ones to pay attention to.

However, since the majority of issues with esbonio appear to be related to Sphinx configs and environment setup, ``v2.x`` goes one step further and by default only shows messages associated with the following LSP methods:

- ``initialize``
- ``initialized``
- ``textDocument/didOpen``
- ``workspace/didChangeConfiguration``

Which results in the following output

.. code-block:: none
   :class: limit-height

   [initialized()][esbonio.Configuration] ConfigurationContext(file_scope='', workspace_scope='')
   [initialized()][esbonio.Configuration] esbonio.server.completion: {
   "preferredInsertBehavior": "replace"
   }
   [initialized()][esbonio.Configuration] CompletionConfig(preferred_insert_behavior='replace')
   [initialized()][esbonio.Configuration] Previous: None
   [initialized()][esbonio.Configuration] Current: CompletionConfig(preferred_insert_behavior='replace')
   [initialized()][esbonio.Configuration] ConfigChangeEvent(scope='', value=CompletionConfig(preferred_insert_behavior='replace'), previous=None)
   [initialized()][esbonio] Task finished: <Task finished name='Task-23' coro=<PreviewManager.show_preview_uri() done, defined at /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/server/features/preview_manager/__init__.py:187> result=None>
   Running Sphinx v9.1.0
   loading translations [en]... done
   The configuration has changed (2 options: 'html_static_path', 'pygments_dark_style')
   loading pickled environment... done
   myst v5.0.0: MdParserConfig(commonmark_only=False, gfm_only=False, enable_extensions=set(), disable_syntax=[], all_links_external=False, links_external_new_tab=False, url_schemes=('http', 'https', 'mailto', 'ftp'), ref_domains=None, fence_as_directive=set(), number_code_blocks=[], title_to_header=False, heading_anchors=0, heading_slug_func=None, html_meta={}, footnote_sort=True, footnote_transition=True, words_per_minute=200, substitutions={}, linkify_fuzzy_links=True, dmath_allow_labels=True, dmath_allow_space=True, dmath_allow_digits=True, dmath_double_inline=False, update_mathjax=True, mathjax_classes='tex2jax_process|mathjax_process|math|output_area', enable_checkboxes=False, suppress_warnings=[], highlight_code_blocks=True)
   /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/sphinx_agent/handlers/domains.py:281: RemovedInSphinx10Warning: The iter() interface for _InventoryItem objects is deprecated. Please access the `project_name`, `project_version`, `uri`, and `displayname` attributes directly.
   (name, version, _, _) = next(iter(next(iter(project.values())).values()))
   /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/sphinx_agent/handlers/domains.py:303: RemovedInSphinx10Warning: The iter() interface for _InventoryItem objects is deprecated. Please access the `project_name`, `project_version`, `uri`, and `displayname` attributes directly.
   for objname, (_, _, item_uri, display) in items.items():
   [initialized()][esbonio.SphinxManager] SphinxClient[0f684895-d015-46f9-ac3b-623c654a720b]: ClientState.Starting -> ClientState.Running
   [initialized()][esbonio.ProjectManager] Registered project for scope 'file:///workspaces/develop/docs': '/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml/esbonio.db'
   [client] sphinx/appCreated: {
   "version": "9.1.0",
   "python": "3.14.3",
   "conf_dir": "/workspaces/develop/docs",
   "build_dir": "/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml",
   "builder_name": "dirhtml",
   "src_dir": "/workspaces/develop/docs",
   "dbpath": "/home/vscode/.cache/esbonio/20e782cab5bb1a14bf2d7b72e76dae1a/dirhtml/esbonio.db"
   }
   [initialized()][esbonio] Task finished: <Task finished name='Task-17' coro=<SphinxManager._create_or_replace_client() done, defined at /workspaces/develop/.vscode/extensions/esbonio/bundled/libs/esbonio/server/features/sphinx_manager/manager.py:316> result=None>

While it is far from perfect, hopefully these changes are at least the start of making the process of diagnosing issues with esbonio more approachable.

Finally, ``v2.x`` introduces the :esbonio:conf:`esbonio.logging.enabledMethods` option which can be used to change the list of LSP methods to show messages for.
