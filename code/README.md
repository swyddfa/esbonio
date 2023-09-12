# Esbonio ![Visual Studio Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/swyddfa.esbonio?style=flat-square)

The Esbonio extension integrates the [`esbonio`](https://pypi.org/project/esbonio/) language server into VSCode.

The `esbonio` language server aims to make it easier to work with [Sphinx](https://www.sphinx-doc.org/en/master/) documentation projects by bringing IDE-like features to your documentation.

## Features

### Live Preview

The extension can show a live HTML preview of the documentation

![HTML Preview](../resources/images/vscode-preview-demo.gif)

### Completions

The language server can provide completion suggestions in various contexts

![Completion Demo](../resources/images/completion-demo.gif)

### Goto Defintion

Goto definition is currently implemented for objects linked to by
`:ref:` and `:doc:` roles

![Goto Defintion Demo](../resources/images/definition-demo.gif)

### Goto Implementation

Goto implementation is available for roles and directives

![Goto Implementation Demo](../resources/images/implementation-demo.gif)
### Diagnostics

Errors from a build are published to VSCode as diagnostics

![Diagnostics](../resources/images/diagnostic-sphinx-errors-demo.png)

### Hover

Documentation is provided for certain roles and directives

![Hover](../resources/images/hover-demo.png)

### Outline

Sections within a document are displayed in the "Outline" view

![Document Outline](../resources/images/document-symbols-demo.png)

## Alternatives

The [reStructuredText](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext) extension  as of [v171.0.0](https://github.com/vscode-restructuredtext/vscode-restructuredtext/releases/tag/171.0.0) also integrates the `esbonio` language server into VSCode.
It also integrates other tools such as the linters [`doc8`](https://pypi.org/project/doc8/) and [`rstcheck`](https://pypi.org/project/rstcheck/) and provides additional editor functionality for working with reStructuredText in general.
