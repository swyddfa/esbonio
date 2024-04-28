<p align="center">
  <img src="./resources/io.github.swyddfa.Esbonio.svg" alt="Esbonio Project Logo"></img>
</p>
<h1 align="center">Esbonio</h1>

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/swyddfa/esbonio/develop.svg)](https://results.pre-commit.ci/latest/github/swyddfa/esbonio/develop)

**esbonio - (v.) to explain**

[reStructuredText]: https://docutils.sourceforge.io/rst.html
[Sphinx]: https://www.sphinx-doc.org/en/master/
[Language Server]: https://langserver.org/

Esbonio aims to make it easier to work with [reStructuredText] tools such as [Sphinx] by providing a [Language Server] to enhance your editing experience.
The Esbonio project is made up from a number of sub-projects


## `lib/esbonio/` - A Language Server for Sphinx projects.

[![PyPI](https://img.shields.io/pypi/v/esbonio?style=flat-square)![PyPI - Downloads](https://img.shields.io/pypi/dm/esbonio?style=flat-square)](https://pypistats.org/packages/esbonio)[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/swyddfa/esbonio/blob/develop/lib/esbonio/LICENSE)

The language server provides the following features.

**Completion**

<p align="center">
  <img src="./resources/images/completion-demo.gif" alt="Completion Suggestions Demo"></img>
</p>

**Definitions**

<p align="center">
  <img src="./resources/images/definition-demo.gif" alt="Goto Definition Demo"></img>
</p>

**Diagnostics**

<p align="center">
  <img src="./resources/images/diagnostic-sphinx-errors-demo.png" alt="Diagnostics Demo"></img>
</p>

**Document Links**

<p align="center">
  <img src="./resources/images/document-links-demo.png" alt="Document Links Demo"></img>
</p>


**Document & Workspace Symbols**

<p align="center">
  <img src="./resources/images/document-workspace-symbols-demo.png" alt="Document & Workspace Symbols Demo"></img>
</p>

**Hover**

<p align="center">
  <img src="./resources/images/hover-demo.png" alt="Hover Demo"></img>
</p>

**Implementations**

<p align="center">
  <img src="./resources/images/implementation-demo.gif" alt="Implementations Demo"></img>
</p>


## `code/` - A VSCode extension for editing Sphinx projects

[![Visual Studio Marketplace Version](https://img.shields.io/visual-studio-marketplace/v/swyddfa.esbonio?style=flat-square)![Visual Studio Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/swyddfa.esbonio?style=flat-square)![Visual Studio Marketplace Downloads](https://img.shields.io/visual-studio-marketplace/d/swyddfa.esbonio?style=flat-square)](https://marketplace.visualstudio.com/items?itemName=swyddfa.esbonio)[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/swyddfa/esbonio/blob/develop/code/LICENSE)

<p align="center">
   <img src="./resources/images/vscode-preview-demo.gif" alt="HTML Preview Demo"></img>
</p>

This extension integrates the `esbonio` language server into VSCode, it's primary goal is to expose all of the features provided by the language server and serve as a reference for integrating `esbonio` into other editors.
Features that cannot be implemented primarily within the language server itself are out of scope for this extension.

For that reason, the Esbonio extension tries to integrate into the wider VSCode ecosystem where possible.

### Dependent Extensions

Esbonio depends on the following extensions

- By default, Esbonio relies on the offical [Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) to configure the environment in which it builds your documentation.

- The [MyST Syntax Highlighting](https://marketplace.visualstudio.com/items?itemName=chrisjsewell.myst-tml-syntax) extension provides syntax highlighting rules for MyST flavoured markdown.

### Supplementry Extensions

The the following extensions are not required in order to use Esbonio, but you might find them useful

- The [reStructuredText](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext) integrates many other useful tools such as the traditional linters like [`doc8`](https://pypi.org/project/doc8/) and [`rstcheck`](https://pypi.org/project/rstcheck/).
  It also provides additional editor functionality for working with reStructuredText in general.

- While VSCode has included a vendored copy of the [reStructuredText Syntax highlighting](https://marketplace.visualstudio.com/items?itemName=trond-snekvik.simple-rst) extension since `v1.66`, installing the extension from the marketplace will provide you with the latest version of the syntax definition.

## `lib/esbonio-extensions/` - A collection of Sphinx extensions

[![PyPI](https://img.shields.io/pypi/v/esbonio-extensions?style=flat-square)![PyPI - Downloads](https://img.shields.io/pypi/dm/esbonio-extensions?style=flat-square)](https://pypistats.org/packages/esbonio-extensions)[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/swyddfa/esbonio/blob/develop/lib/esbonio-extensions/LICENSE)
