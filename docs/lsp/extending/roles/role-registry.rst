Supporting Custom Role Registries
=================================

.. currentmodule:: esbonio.lsp.roles

This guide walks through the process of teaching the language server how to discover roles stored in a custom registry.
Once complete, the following LSP features should start working with your roles.

- Basic role completions i.e. ``:role-name:`` but no target completions.
- Documentation hovers (assuming you've provided documentation)
- Goto Implementation

.. note::

   You may not need this guide.

   If you're registering your role directly with
   `docutils <https://docutils.sourceforge.io/docs/howto/rst-roles.html#register-the-role>`__ or
   `sphinx <https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_role>`__,
   or using a `custom domain <https://www.sphinx-doc.org/en/master/extdev/domainapi.html>`__
   then you should find that the language server already has basic support for your custom roles out of the box.

   This guide is indended for adding support for roles that are not registered in a standard location.

Still here? Great! Let's get started.

Indexing Roles
--------------

As an example, we'll walk through the steps required to add (basic) support for Sphinx domains to the language server.

.. note::

   For the sake of brevity, some details have been omitted from the code examples below.

   If you're interested, you can find the actual implementation of the ``DomainRoles`` class
   `here <https://github.com/swyddfa/esbonio/blob/release/lib/esbonio/esbonio/lsp/sphinx/domains.py>`__.

So that the server can discover the available roles, we have to provide a :class:`RoleLanguageFeature` that implements the :meth:`~RoleLanguageFeature.index_roles` method.
This method should return a dictionary where the keys are the canonical name of the role which map to the function that implements it::

   class DomainRoles(RoleLanguageFeature):
       def __init__(self, app: Sphinx):
           self.app = app   # Sphinx application instance.

       def index_roles(self) -> Dict[str, Any]:
           roles = {}
           for prefix, domain in self.app.domains.items():
               for name, role in domain.roles.items():
                   roles[f"{prefix}:{name}"] = role

           return roles

In the case of Sphinx domains a role's canonical name is of the form ``<domain>:<role>`` e.g. ``py:func`` or ``c:macro``.

This is the bare minimum required to make the language server aware of your custom roles, in fact if you were to try the above implementation you would already find completions being offered for domain based roles.
However, you would also notice that the short form of roles (e.g. ``func``) in the :ref:`standard <sphinx:domains-std>` and :confval:`primary <sphinx:primary_domain>` domains are not included in the list of completions - despite being valid.

To remedy this, you might be tempted to start adding multiple entries to the dictionary, one for each valid name **do not do this.**
Instead you can implement the :meth:`~RoleLanguageFeature.suggest_roles` method which solves this exact use case.

.. tip::

   If you want to play around with your own version of the ``DomainRoles`` class you can disable the built in version by:

   - Passing the ``--exclude esbonio.lsp.sphinx.domains`` cli option, or
   - If you're using VSCode adding ``esbonio.lsp.sphinx.domains`` to the :confval:`esbonio.server.excludedModules (string[])` option.

(Optional) Suggesting Roles
---------------------------

The :meth:`~RoleLanguageFeature.suggest_roles` method is called each time the server is generating role completions.
It can be used to tailor the list of roles that are offered to the user, depending on the current context.
Each ``RoleLanguageFeature`` has a default implementation, which may be sufficient depending on your use case::

   def suggest_roles(self, context: CompletionContext) -> Iterable[Tuple[str, Any]]:
       """Suggest roles that may be used, given a completion context."""
       return self.index_roles().items()

However, in the case of Sphinx domains, we need to modify this to also include the short form of the roles in the standard and primary domains::

   def suggest_roles(self, context: CompletionContext) -> Iterable[Tuple[str, Any]]:
       roles = self.index_roles()
       primary_domain = self.app.config.primary_domain

       for key, role in roles.items():

           if key.startswith("std:"):
               roles[key.replace("std:", "")] = role

           if primary_domain and key.startswith(f"{primary_domain}:"):
               roles[key.replace(f"{primary_domain}:", "")] = role

      return roles.items()

Now if you were to try this version, the short forms of the relevant directives would be offered as completion suggestions, but you would also notice that features like documentation hovers still don't work.
This is due to the language server not knowing which class implements these short form directives.

(Optional) Implementation Lookups
---------------------------------

The :meth:`~RoleLanguageFeature.get_implementation` method is used by the language server to take a role's name and lookup its implementation.
This powers features such as documentation hovers and goto implementation.
As with ``suggest_roles``, each ``RoleLanguageFeature`` has a default implementation which may be sufficient for your use case::

    def get_implementation(self, role: str, domain: Optional[str]) -> Optional[Any]:
        """Return the implementation for the given role name."""
        return self.index_roles().get(role, None)

In the case of Sphinx domains, if we see a directive without a domain prefix we need to see if it belongs to the standard or primary domains::

    def get_implementation(self, role: str, domain: Optional[str]) -> Optional[Any]:
        roles = self.index_roles()

        if domain is not None:
            return roles.get(f"{domain}:{role}", None)

        primary_domain = self.app.config.primary_domain
        impl = roles.get(f"{primary_domain}:{role}", None)
        if impl is not None:
            return impl

        return roles.get(f"std:{role}", None)
