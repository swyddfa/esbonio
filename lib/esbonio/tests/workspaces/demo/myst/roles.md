# Roles

This page provides an overview of the features Esbonio provides to make working with {external+myst:std:ref}`MyST Roles <syntax/roles>` easier.

(myst-roles-completion)=
## Completion

The most obvious feature is the completion suggestions, try inserting a `{ref}` role on the next line that links to the `myst-roles-completion` label defined above.

% Add your reference here...

In addition to `:ref:` labels, `esbonio` supports suggesting values for many other types of target

- Local docnames for the {external:rst:role}`doc` role
- Local filenames for the {external:rst:role}`download` role
- Python objects for roles like {external:rst:role}`py:class`, {external:rst:role}`py:func` and more!
- Targets defined in *other* Sphinx documentation sites for the {external:rst:role}`external` role!
  See {external:std:ref}`ext-intersphinx` for more details

Feel free to experiment with each of the roles mentioned above!

## Document Links

Many text editors will automatically detect links to webpages e.g. https://sphinx-doc.org and make them clickable.
The [textDocument/documentLink](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentLink) request allows language servers to do the same.

When it makes sense to, `esbonio` will add clickable links to many role targets, including

- {doc}`Local docname references </rst/roles>`
- Local files {download}`./roles.md`
- Intersphinx references e.g. {external:std:ref}`logging-exceptions`

See for yourself by pressing `Ctrl` +Clicking one of the above references

## GoTo ...

### ... Definition

Esbonio supports GoTo Definition requests for role targets, including

- Local files {download}`./roles.md`
- Documents {doc}`/myst/roles`
- References {ref}`rst-roles-completion`
- Python objects {py:class}`counters.pattern.PatternCounter`

Try invoking GoTo Definition on any of the above targets.

## Hover

Esbonio provides documentation hovers for role targets, including:

- Local Python objects, for example:

  - {py:class}`counters.pattern.PatternCounter`
  - {py:meth}`counters.pattern.PatternCounter.fromstr`
  - {py:obj}`counters.pattern.DEFAULT_PATTERN`

Hover over any of the above targets to see their associated content.
