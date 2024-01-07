# Esbonio

[![Stable Version](https://img.shields.io/visual-studio-marketplace/v/swyddfa.esbonio.svg?label=stable&color=&style=flat-square)](https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio)
[![Install Count](https://img.shields.io/visual-studio-marketplace/i/swyddfa.esbonio.svg?style=flat-square)](https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio)
[![Download Count](https://img.shields.io/visual-studio-marketplace/d/swyddfa.esbonio.svg?style=flat-square)](https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio)
![Pre-release Version](https://img.shields.io/visual-studio-marketplace/v/swyddfa.esbonio?include_prereleases&label=pre-release&style=flat-square)

The Esbonio extension integrates the [`esbonio`](https://pypi.org/project/esbonio/) language server into VSCode.

The `esbonio` language server aims to make it easier to work with [Sphinx](https://www.sphinx-doc.org/en/master/) documentation projects by bringing IDE-like features to your documentation experience.

## Features

### Live Preview

The extension can show a live HTML preview of the documentation, so the preview contents change whenever the document is updated

![HTML Preview](../resources/images/vscode-preview-demo.gif)

### Completions

The language server can provide completion suggestions in various contexts

![Completion Demo](../resources/images/completion-demo.gif)

### Goto Definition

Goto definition is currently implemented for objects linked to by
`:ref:` and `:doc:` roles

![Goto Definition Demo](../resources/images/definition-demo.gif)

### Goto Implementation

Goto implementation is available for roles and directives

![Goto Implementation Demo](../resources/images/implementation-demo.gif)
### Diagnostics

Errors from a build are published to VSCode as diagnostics

![Diagnostics](../resources/images/diagnostic-sphinx-errors-demo.png)

### Hover

Documentation is provided for certain roles and directives when the cursor hovers over them in the editor

![Hover](../resources/images/hover-demo.png)

### Outline

Sections within a document are displayed in the "Outline" view

![Document Outline](../resources/images/document-symbols-demo.png)

## Supplement Extensions

The [reStructuredText](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext) extension as of [v190.1.17](https://github.com/vscode-restructuredtext/vscode-restructuredtext/releases/tag/190.1.17) integrates many other useful tools such as the traditional linters like [`doc8`](https://pypi.org/project/doc8/) and [`rstcheck`](https://pypi.org/project/rstcheck/). It also provides additional editor functionality for working with reStructuredText in general. More details can be found on the [extension's page](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext).

The [reStructuredText Syntax highlighting](https://marketplace.visualstudio.com/items?itemName=trond-snekvik.simple-rst) extension provides syntax highlighting for reStructuredText files. More details can be found on the [extension's page](https://marketplace.visualstudio.com/items?itemName=trond-snekvik.simple-rst).
