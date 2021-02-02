# Esbonio ![Visual Studio Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/swyddfa.esbonio?style=flat-square)

**This extension is in early development**

Esbonio is an extension that provides a language server for working with
[Sphinx](https://www.sphinx-doc.org/en/master/) documentation projects.

## Setup

So that the language server can be updated independently of this extension, it is not
currently bundled with it. Instead it is distributed as a package on
[PyPi](https://pypi.org/project/esbonio/) that must be installed into the same Python
environment as the one you use to build your Sphinx project. This is so that the server is
able to wrap an instance of Sphinx as per your project's config, inspect it, and expose it via the LSP Protocol.

The extension does its best to automate this process, installing the server into the python
environment you have configured in the
[Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) by
default. If however, you don't have the Python extension installed or you want to use a
different Python environment for your documentation there is a configuration option
`esbonio.pythonPath` that you can use to set the environment.

![Setup Demo](../resources/images/vscode-setup-demo.gif)

## Features

### Completions

The language server can provide completion suggestions in various contexts
#### Directives

Completion suggestions are offered for the directives themselves, as well as any options
that they expose.

![Directive Completions](../resources/images/complete-directive-demo.gif)

#### Roles

In the case of roles, completions can also be offered for the targets of certain
[supported](https://swyddfa.github.io/esbonio/docs/lsp/features.html#roles) role types

![Role Completions](../resources/images/complete-role-demo.gif)

#### Inter Sphinx

The [intersphinx](https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html)
extension can be used to easily link to other Sphinx projects. If configured, the language
server will offer suggestions when appropriate

![InterSphinx Completions](../resources/images/complete-intersphinx-demo.gif)

### Diagnostics

Errors from a build are published to VSCode as diagnostics

![Diagnostics](../resources/images/diagnostic-sphinx-errors-demo.png)

### Syntax Highlighting

This extension also offers a simple grammar definition to enable some basic
syntax highlighting

![Syntax Highlighting](../resources/images/syntax-highlighting-demo.png)

## Alternatives

This project was created to scratch an itch, if it happens to also scratch an itch
for you then great! If not, here are some alternatives you may wish to consider

- [reStructuredText](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext)
