# Symbols

```{admonition} What is a symbol?

In LSP a "symbol", is any sequence of characters that have a particular meaning to the file format you are currently working in.
In programming languages this could include keywords, variables, type definitions etc.

`esbonio` currently identifies section headers and directives as symbols.
```

The language server supports both {lsp}`textDocument/documentSymbol` and {lsp}`workspace/symbol` requests.

## Document Symbols

As the name suggests, the `textDocument/documentSymbol` request returns all the symbols contained in a given file.
The server can also include hierarchical information about the symbols, e.g. The symbol `Sub-section` is contained within the symbol `Section`.

In VSCode this information is typically used to populate the {guilabel}`Outline` view.
You can also search for a symbol in the current document using the {kbd}`Ctrl+Shift+O` keybinding.

```{note}

In the case of MyST, both `Esbonio` and VSCode's built-in `Markdown Language Features` provide this information, so you will most likely see two similar symbol hierarchies.

If you know how to configure VSCode to hide one or the other we'd like to know!
```

## Workspace Symbols

The `workspace/symbol` request allows your editor to ask Esbonio to search through all the symbols is has found in your workspace.
Unlike the `textDocument/documentSymbol` request there is no hierarchy information included and results are a simple flat list.

Depending on what a symbol represents, Esbonio will allow you to search for symbols by different criteria.

- For sections, you can only search for the section name itself.
- For directives you can search either by the directive's name e.g. `figure::` or its argument e.g. `/images/screenshot.jpg`

In VSCode, you can perform a workspace symbol search by pressing {kbd}`Ctrl+T`.
