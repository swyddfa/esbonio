# Bring your own Sphinx

While the `esbonio` language server is bundled as part of the extension, it does *not* include an installation of Sphinx.

This is because every Sphinx project is unique with its own set of dependencies and required extensions. In order to correctly understand your project `esbonio` needs to use the same Python environment that you use to build your documentation.

You can tell Esbonio which environment to use by setting the `esbonio.sphinx.pythonCommand` option. See [this guide](https://docs.esbon.io/en/latest/lsp/howto/use-esbonio-with.html) for some examples
