<p align="center">
  <img src="./resources/io.github.swyddfa.Esbonio.svg" alt="Esbonio Project Logo"></img>
</p>
<h1 align="center">Esbonio</h1>

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/swyddfa/esbonio/develop.svg)](https://results.pre-commit.ci/latest/github/swyddfa/esbonio/develop)

**esbonio - (v.) to explain**

Esbonio aims to make it easier to work with [reStructuredText](https://docutils.sourceforge.io/rst.html) tools such as [Sphinx](https://www.sphinx-doc.org/en/master/) by providing a [Language Server](https://langserver.org/) to enhance your editing experience.
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
  <img src="https://private-user-images.githubusercontent.com/2675694/292643698-0313faec-51e8-4721-96d7-6655dd097e0d.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MDQwNDk3NTcsIm5iZiI6MTcwNDA0OTQ1NywicGF0aCI6Ii8yNjc1Njk0LzI5MjY0MzY5OC0wMzEzZmFlYy01MWU4LTQ3MjEtOTZkNy02NjU1ZGQwOTdlMGQucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDIzMTIzMSUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyMzEyMzFUMTkwNDE3WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MzM4ZTI2NmU4MjMxMDdkNzg0NTljZmY3YmZiOTkyZDk4YzRiMmIwYjE3ZmYzM2ZjYTE0ZWQ1MzE2MDQwNWViOCZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QmYWN0b3JfaWQ9MCZrZXlfaWQ9MCZyZXBvX2lkPTAifQ.6wPVjBj3NijMyDtaWP3vEE55vGHHt9wC0XGFMiImo1Q" alt="Document Symbols Demo"></img>
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

This extension is purely focused on bringing the `esbonio` language server into VSCode to help with development and testing new ideas.

### You're probably looking for the reStructuredText Extension

You may already be familiar with the [reStructuredText](https://marketplace.visualstudio.com/items?itemName=lextudio.restructuredtext) extension which, as of [v171.0.0](https://github.com/vscode-restructuredtext/vscode-restructuredtext/releases/tag/171.0.0) now also integrates the `esbonio` language server into VSCode.
It also integrates other tools such as the linters [`doc8`](https://pypi.org/project/doc8/) and [`rstcheck`](https://pypi.org/project/rstcheck/) and provides additional editor functionality making it easier to work with reStructuredText in general.

**Wait.. so why does the Esbonio VSCode extension still exist?**

The reStructuredText extension takes a more conservative approach to adopting new VSCode features and APIs leaving the Esbonio extension free to more aggressively follow new developments.
The Esbonio extension is developed alongside the language server itself, which allows for easy testing of new features without waiting for downstream projects to catch up.
Finally, the Esbonio extension serves as an up to date reference for projects that integrate `esbonio` into other editors.

**That sounds great... but which extension is right for me?**

Try the reStructuredText extension if

- You need an extension compatible with older versions of VSCode
- You are looking for a more rounded editing experience.

Try the Esbonio extension if

- You want to make use of the newer features available in recent VSCode versions
- You are only interested in the features provided by the language server

## `lib/esbonio-extensions/` - A collection of Sphinx extensions
[![PyPI](https://img.shields.io/pypi/v/esbonio-extensions?style=flat-square)![PyPI - Downloads](https://img.shields.io/pypi/dm/esbonio-extensions?style=flat-square)](https://pypistats.org/packages/esbonio-extensions)[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/swyddfa/esbonio/blob/develop/lib/esbonio-extensions/LICENSE)
