Supporting Custom Directive Registries
======================================

.. currentmodule:: esbonio.lsp.directives

This guide walks through the process of teaching the language server how to discover directives stored in a custom registry.
Once complete, the following LSP features should start working with your directives.

- Basic directive completions i.e. ``.. directive-name::`` but no argument completions.
- Basic option key completions i.e. ``:option-name:`` assuming options are declared in a directive's ``option_spec``, but no option value completions.
- Documentation hovers assuming you've provided documentation.
- Goto Implementation.

.. note::

   You may not need this guide.

   If you're registering your directive directly with
   `docutils <https://docutils.sourceforge.io/docs/howto/rst-directives.html#register-the-directive>`__ or
   `sphinx <https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_directive>`__,
   or using a `custom domain <https://www.sphinx-doc.org/en/master/extdev/domainapi.html>`__
   then you should find that the language server already has basic support for your custom directives out of the box.

   This guide is indended for adding support for directives that are not registered in a standard location.

Still here? Great! Let's get started.

Indexing Directives
-------------------

As an example, we'll walk through the steps required to add (basic) support for Sphinx domains to the language server.

.. note::

   For the sake of brevity, some details have been omitted from the code examples below.

   If you're interested, you can find the actual implementation of the ``DomainDirectives`` class
   `here <https://github.com/swyddfa/esbonio/blob/release/lib/esbonio/esbonio/lsp/sphinx/domains.py>`__.

So that the server can discover the available directives, we have to provide a :class:`DirectiveLanguageFeature` that implements the :meth:`~DirectiveLanguageFeature.index_directives` method.
This method should return a dictionary where the keys are the canonical name of a directive which map to the class that implements it::

   class DomainDirectives(DirectiveLanguageFeature):
       def __init__(self, app: Sphinx):
           self.app = app  # Sphinx application instance.

       def index_directives(self) -> Dict[str, Directive]:
           directives = {}
           for prefix, domain in self.app.domains.items():
               for name, directive in domain.directives.items():
                   directives[f"{prefix}:{name}"] = directive

           return directives

In the case of Sphinx domains a directive's canonical name is of the form ``<domain>:<directive>`` e.g. ``py:function`` or ``c:macro``.

This is the bare minimum required to make the language server aware of your custom directives, in fact if you were to try the above implementation you would already find completions being offered for domain based directives.
However, you would also notice that the short form of directives (e.g. ``function``) in the :ref:`standard <sphinx:domains-std>` and :confval:`primary <sphinx:primary_domain>` domains are not included in the list of completions - despite being valid.

To remedy this, you might be tempted to start adding multiple entries to the dictionary, one for each valid name **do not do this.**
Instead you can implement the :meth:`~DirectiveLanguageFeature.suggest_directives` method which solves this exact use case.

.. tip::

   If you want to play around with your own version of the ``DomainDirectives`` class you can disable the built in version by:

   - Passing the ``--exclude esbonio.lsp.sphinx.domains`` cli option, or
   - If you're using VSCode adding ``esbonio.lsp.sphinx.domains`` to the :confval:`esbonio.server.excludedModules (string[])` option.

(Optional) Suggesting Directives
--------------------------------

The :meth:`~DirectiveLanguageFeature.suggest_directives` method is called each time the server is generating directive completions.
It can be used to tailor the list of directives that are offered to the user, depending on the current context.
Each ``DirectiveLanguageFeature`` has a default implementation, which may be sufficient depending on your use case::

   def suggest_directives(self, context: CompletionContext) -> Iterable[Tuple[str, Directive]]:
       return self.index_directives().items()

However, in the case of Sphinx domains, we need to modify this to also include the short form of the directives in the standard and primary domains::

   def suggest_directives(self, context: CompletionContext) -> Iterable[Tuple[str, Directive]]:
       directives = self.index_directives()
       primary_domain = self.app.config.primary_domain

       for key, directive in directives.items():

           if key.startswith("std:"):
               directives[key.replace("std:", "")] = directive

            if primary_domain and key.startswith(f"{primary_domain}:"):
               directives[key.replace(f"{primary_domain}:", "")] = directive

        return directives.items()

Now if you were to try this version, the short forms of the relevant directives would be offered as completion suggestions, but you would also notice that features like documentation hovers still don't work.
This is due to the language server not knowing which class implements these short form directives.

(Optional) Implementation Lookups
---------------------------------

The :meth:`~DirectiveLanguageFeature.get_implementation` method is used by the language server to take a directive's name and lookup its implementation.
This powers features such as documentation hovers and goto implementation.
As with ``suggest_directives``, each ``DirectiveLanguageFeature`` has a default implementation which may be sufficient for your use case::

   def get_implementation(self, directive: str, domain: Optional[str]) -> Optional[Directive]:
       return self.index_directives().get(directive, None)

In the case of Sphinx domains, if we see a directive without a domain prefix we need to see if it belongs to the standard or primary domains::

   def get_implementation(self, directive: str, domain: Optional[str]) -> Optional[Directive]:
       directives = self.index_directives()

       if domain is not None:
           return directives.get(f"{domain}:{directive}", None)

       primary_domain = self.app.config.primary_domain
       impl = directives.get(f"{primary_domain}:{directive}", None)
       if impl is not None:
           return impl

       return directives.get(f"std:{directive}", None)
