# Scripts

This folder contains a number of scripts that are either useful during
development or for automating project management tasks.

| Name | Description |
|-|-|
| `generate_docutils_documentation.py` | This script is used to scrape the docutils documentation site for documentation on roles and directives that the language server can attach to `CompletionItems` |
| `generate_sphinx_documentation.py` | This script is used to scrape the sphinx documentation site for documentation on roles and directives that the language server can attach to `CompletionItems` |
| `make-release.sh` | As the name suggests this script is responsible for automating parts of a release, including tasks such as setting the version number, tagging the release and writing the changelog. |
| `preview_documentation.py` | While JSON is a useful documentation format for the language server, it's not great for humans. This is a simple [Textual]() app that makes it easy to see the results of the `generate_xxxx_documentation.py` scripts. |
| `project-management.sh` | This script is run from GitHub Actions to automatically assign issues to the relevant projects based on labels. |
| `should-build.sh` | Being a monorepo, not all changes require all CI pipelines to be run. This script is used by Github Actions to determine which pipelines should be run on any given PR |
| `sphinx-app.py` | Useful when you want to inspect Sphinx's internals, this is used to bootstrap a REPL with a Sphinx application instance configured for our `docs/`. <br /> Usage: `python -i sphinx-app.py` |
| `check-sphinx-version.py` | Check that we are testing the correct Sphinx version inside tox. |
