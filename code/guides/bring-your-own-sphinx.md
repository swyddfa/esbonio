# Bring your own Sphinx

While the `esbonio` language server itself is included as part of the Esbonio extension, it does *not* include an installation of Sphinx.

This is because every Sphinx project is unique with its own set of dependencies and required extensions. So in order to correctly understand your project `esbonio` needs to use the same Python environment that you use to build your documentation.

The Esbonio extension supports two mechanisms for selecting your Python environment.

1. If the official Python extension is available, by default Esbonio will attempt to use the same environment you have configured for your workspace.
2. Alternatively, you can use the `esbonio.sphinx.pythonCommand` setting to override this behavior.
