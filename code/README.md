# Esbonio ![Visual Studio Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/swyddfa.esbonio?style=flat-square)

The Esbonio extension integrates the [`esbonio`](https://pypi.org/project/esbonio/) language server into VSCode.

The `esbonio` language server aims to make it easier to work with [Sphinx](https://www.sphinx-doc.org/en/master/) documentation projects by providing completion suggestions for your cross references and many other features.

## What about the reStructuredText Extension?

You may already be familiar with the [reStructuredText](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext) extension which, as of [v171.0.0](https://github.com/vscode-restructuredtext/vscode-restructuredtext/releases/tag/171.0.0) now also integrates the `esbonio` language server into VSCode.
It also integrates other tools such as the linters [`doc8`](https://pypi.org/project/doc8/) and [`rstcheck`](https://pypi.org/project/rstcheck/) and provides additional editor functionality making it easier to work with reStructuredText in general.

**Wait.. so why does the Esbonio VSCode extension still exist?**

The reStructuredText extension takes a more conservative approach to adopting new VSCode features and APIs leaving the Esbonio extension free to more aggressively follow new developments.
The Esbonio extension is developed alongside the language server itself, which allows for easy testing of new features without waiting for downstream projects to catch up.
Finally, the Esbonio extension serves as an up to date reference for projects that integrate `esbonio` into other editors.

**That sounds great... but which extension is right for me?**

Try the reStructuredText extension if

- You need an extension compatible with older versions of VSCode
- You are interested in additional features beyond what is provided by the language server

Try the Esbonio extension if

- You want to make use of the newer features available in recent VSCode versions
- You are only interested in the features provided by the language server

## Features

### Preview

The extension can show a HTML preview of the documentation

![HTML Preview](../resources/images/vscode-preview-demo.gif)

### Completions

The language server can provide completion suggestions in various contexts

![Completion Demo](../resources/images/completion-demo.gif)

### Goto Defintion

Goto definition is currently implemented for objects linked to by
`:ref:` and `:doc:` roles

![Goto Defintion Demo](../resources/images/definition-demo.gif)

### Diagnostics

Errors from a build are published to VSCode as diagnostics

![Diagnostics](../resources/images/diagnostic-sphinx-errors-demo.png)

### Hover

Documentation is provided for certain roles and directives

![Hover](../resources/images/hover-demo.png)

### Outline

Sections within a document are displayed in the "Outline" view

![Document Outline](../resources/images/document-symbols-demo.png)

### Syntax Highlighting

Syntax Highlighting is provided thanks to the [reStructuredText Syntax Highlighting Extension](https://marketplace.visualstudio.com/items?itemName=trond-snekvik.simple-rst) extension.

## Setup

The language server works by wrapping an instance of Sphinx's application object,
inspecting it and exposing the results over the Language Service Protocol. As Sphinx is
a Python application this also dictates thats the Language Server is written in Python
and distributed as a package on [PyPi](https://pypi.org/project/esbonio/).

In order to correctly wrap your Sphinx application this requires the Language Server be
installed into the same environment as the one that you use to build your
documentation.

There are a number of ways this can be accomplished.

### Automatically

The extension does its best to automate the installation and application of updates to the
Language Server. By default Esbonio will use the Python environment you have configured
[Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
when installing and running the server. If however, you don't have the Python extension
installed or you want to use a different Python environment for your documentation there
is a configuration option `esbonio.server.pythonPath` that you can use to configure the
environment.

There are a number of configuration options that allow you to control exactly how
installation and updates are handled. See the
[documentation](https://swyddfa.github.io/esbonio/docs/lsp/editors/vscode.html#configuration)
for more details.

![Setup Demo](../resources/images/vscode-setup-demo.gif)

### Manually

Alternatively you can opt to manage the installation of the language server entirely
yourself. To install the Lanaguage Server open the terminal in your desired Python
environment and run

```
(env) $ pip install esbonio
```

Then all you have to ensure is that Esbonio is configured to use the same environment,
either through the
[Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
or through the `esbonio.server.pythonPath` configuration option.

To also manage updates manually, be sure to look at the
[documentation](https://swyddfa.github.io/esbonio/docs/lsp/editors/vscode.html#configuration)
for options on how to disable automatic updates.
