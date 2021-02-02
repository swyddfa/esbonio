# Esbonio

**This extension is in early development**

Esbonio is an extension that provides a language server for editing
[Sphinx](https://www.sphinx-doc.org/en/master/) projects.

## Features

### Completions

The language server can provide completion suggestions in various contexts
#### Directives

![Directive Completions](../resources/images/complete-directive-demo.gif)

#### Directive Options

![Directive Option Completions](../resources/images/complete-directive-options-demo.gif)

#### Roles

![Role Completions](../resources/images/complete-role-demo.gif)

#### Role Targets

For some supported role types

![Role Target Completions](../resources/images/complete-role-target-demo.gif)

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
