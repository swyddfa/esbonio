![Esbonio logo](https://github.com/swyddfa/esbonio/blob/release/resources/io.github.swyddfa.Esbonio.svg?raw=true)
# Esbonio

[![PyPI](https://img.shields.io/pypi/v/esbonio?style=flat-square)](https://pypi.org/project/esbonio)[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/esbonio?style=flat-square)](https://pypi.org/project/esbonio)![PyPI - Downloads](https://img.shields.io/pypi/dm/esbonio?style=flat-square)[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/swyddfa/esbonio/blob/develop/lib/esbonio/LICENSE)

**esbonio - (v.) to explain**

A [Language Server](https://microsoft.github.io/language-server-protocol/) that aims to make it easier to work with [reStructuredText](https://docutils.sourceforge.io/rst.html) tools such as [Sphinx](https://www.sphinx-doc.org/en/master/)

> **Important**
>
> The `0.16.x` version of the language server is no longer in active development, all new users are encouraged to start with the `1.0bx` version.
>
> Existing users are also encouraged to [migrate](https://docs.esbon.io/en/latest/lsp/howto/migrate-to-v1.html), unless you are relying on a feature not yet provided by the `1.0bx` version.
> (See [this issue](https://github.com/swyddfa/esbonio/issues/901) for the latest status)
>
> The `1.0` version of the language server will be released once the remaining features from `0.16.x` have been ported across.

## Features

### Completion

![Completion Demo](https://github.com/swyddfa/esbonio/raw/0.x/resources/images/completion-demo.gif)

### Definitions

![Definition Demo](https://github.com/swyddfa/esbonio/raw/0.x/resources/images/definition-demo.gif)


### Diagnostics

![Diagnostics Demo](https://github.com/swyddfa/esbonio/raw/0.x/resources/images/diagnostic-sphinx-errors-demo.png)

### Document Links

![Document Link Demo](https://github.com/swyddfa/esbonio/raw/0.x/resources/images/document-links-demo.png)

### Document Symbols

![Document Symbols](https://github.com/swyddfa/esbonio/raw/0.x/resources/images/document-symbols-demo.png)

### Hover

![Hover Demo](https://github.com/swyddfa/esbonio/raw/0.x/resources/images/hover-demo.png)

### Implementations

![Implementations Demo](https://github.com/swyddfa/esbonio/raw/0.x/resources/images/implementation-demo.gif)

## Installation

The Language Server can be installed via pip.

Be sure to check out the [Getting Started](https://docs.esbon.io/en/esbonio-language-server-v0.16.4/lsp/getting-started.html) guide for details on integrating the server with your editor of choice.

```
$ pip install esbonio
```
