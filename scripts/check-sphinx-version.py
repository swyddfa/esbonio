"""Check that we are testing the correct Sphinx version inside tox."""

import os

import sphinx


def main():
    # The environment name has the form of py310-sphinx5.
    tox_env_name = os.environ.get("TOX_ENV_NAME", "")
    sphinx_version = tox_env_name.split("-", maxsplit=1)[1]
    prefix = "sphinx"
    if sphinx_version.startswith(prefix):
        version = sphinx_version[len(prefix) :]
        assert sphinx.__version__.startswith(
            version
        ), "Sphinx version doesn't match tox environment"


if __name__ == "__main__":
    main()
