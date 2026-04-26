# Configure your `sphinx-build` arguments

By default `esbonio` will choose `sphinx-build` arguments that are roughly equivalent to the following.
```
$ sphinx-build -M dirhtml <project_src> <user_cache_dir>/<project_hash>
```
This can be changed by setting `esbonio.sphinx.buildArguments` in your `pyproject.toml`
```toml
[tool.esbonio.sphinx]
buildArguments = [
    "sphinx-build", "-M", "html", "docs", "${defaultBuildDir}", "--nitpicky", "--verbose",
]
```
Alternatively, you can include the setting in your `.vscode/settings.json`
```json
{
    "esbonio.sphinx.buildArguments": [
        "sphinx-build",
        "-b", "html",
        "-j", "auto",
        "docs", "docs/_build"
    ]
}
```
See [this guide](https://docs.esbon.io/en/latest/usage/howto/configure-the-sphinx-build-cmd.html) for further details.
