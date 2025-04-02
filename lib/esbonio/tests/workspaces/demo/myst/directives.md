# Directives

This page provides an overview of the features Esbonio provides to make working with {external+myst:std:ref}`MyST Directives <syntax/directives>` easier.

## Completion

The most obvious feature is the completion suggestions, try inserting a `{note}` directive on the next line

% Add your note here...

In addition to directive names, Esbonio supports suggesting values many kinds of arguments given to a directive, including.

**Filepaths**

Completing filepath arguments is supported for the following directives

- [`figure`](https://docutils.sourceforge.io/docs/ref/rst/directives.html#figure)
- [`image`](https://docutils.sourceforge.io/docs/ref/rst/directives.html#image)
- [`include`](https://docutils.sourceforge.io/docs/ref/rst/directives.html#image)
- {external+sphinx:rst:dir}`literalinclude`

% Try using the `literalinclude` directive to insert the contents of this project's conf.py here...

**Pygments Lexers**

Sphinx uses the [pygments](https://pygments.org/) library for its syntax highlighting.
Esbonio will offer the names of available lexers as suggestions for the following directives.

- {external+sphinx:rst:dir}`code`
- {external+sphinx:rst:dir}`code-block`
- {external+sphinx:rst:dir}`highlight`
- {external+sphinx:rst:dir}`sourcecode`

Of course MyST allows you to use standard Markdown code blocks as well, Esbonio will also offer suggestions in this context.

% Try inserting a code block on the next line...

## Document Links

Many text editors will automatically detect links to webpages, e.g., <https://sphinx-doc.org>, and make them clickable.
The [`textDocument/documentLink`](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_documentLink) request allows language servers to do the same.

When it makes sense to, `esbonio` will add clickable links to many directive arguments, including:

- Local files

  ````markdown
  ```{include} ./directives.md
  ```
  ````
## GoTo...

### ... Definition

Esbonio supports GoTo Definition requests for directive arguments, including:

- Local files

  ````markdown
  ```{include} ./symbols.md
  ```
  ````
