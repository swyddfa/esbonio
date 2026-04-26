# Bring your own Sphinx

While a minimal Sphinx environment is included with this extension, it's not likely to include all the necessary dependencies for your project.

In order to correctly build and understand your project `esbonio` needs to use the same Python environment that you use to build your documentation.

You can tell Esbonio which environment to use by setting the `esbonio.sphinx.pythonCommand` option.
The recommended way to do this is to update your project's `pyproject.toml` file

```toml
[tool.esbonio.sphinx]
pythonCommand = ["${venv:/path/to/your/venv}"]
```

Alternatively, you can include the setting in your `.vscode/settings.json`

```json
{
    "esbonio.sphinx.pythonCommand": [
        "uv", "run",
        "--no-project",
        "--python", "3.14"
        "--with", "sphinx",
        "--with", "furo",
         "python"
    ]
}
```

See [this guide](https://docs.esbon.io/en/release/usage/howto/configure-the-sphinx-build-env.html) for more examples
