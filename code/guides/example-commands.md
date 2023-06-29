# The `sphinx-build` command


> `usage: sphinx-build [OPTIONS] SOURCEDIR OUTPUTDIR [FILENAMES...]`

Build documentation for the web using the `html` builder, alternatively you can use the `dirhtml` builder if you want "pretty" URLs

- `sphinx-build -M html docs docs/_build`
- `sphinx-build -M dirhtml docs docs/_build`

Here are some additional options you might find useful, these must come **after** the `-M <builder-name>` option.

- `-j auto`: enable parallel builds
- `-a`: write all files, even if their source has not changed
- `-E`: ignore previously saved enironment
- `-c <path>`: use an alternate path to `conf.py`

See `sphinx-build -h` for a comprehensive list of the available options.

> **Important:**
>
> The following options are **not** supported by `esbonio`
> - `-P`: run Pdb on exception
> - `--color, -N, --no-color`: color options
