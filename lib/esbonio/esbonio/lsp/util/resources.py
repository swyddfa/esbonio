import importlib.resources


def read_string(package: str, filename: str) -> str:
    """Light wrapper around ``importlib.resources`` that should work across Python
    versions.

    Parameters
    ----------
    package
       The module/package to read from

    filename
       The file within ``package`` to read

    Returns
    -------
    str
       The contents of the specified text file.
    """

    # `files` only available in Python 3.9+
    if hasattr(importlib.resources, "files"):
        with importlib.resources.files(package).joinpath(filename).open("r") as f:
            return f.read()

    # `open_text` deprecated in Python 3.11, so let's only rely on it when we
    # have to.
    with importlib.resources.open_text(package, filename) as f:
        return f.read()
