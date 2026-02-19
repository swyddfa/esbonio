.. _lsp-use-without-sphinx-project:

How To Use Esbonio without a Sphinx Project
===========================================

Esbonio (currently) requires a background Sphinx process in order to be useful.
However, this does not mean Esbonio can only be used with a "proper" Sphinx project.

This guide provides some examples on how you might configure Esbonio for "lightweight" or single file projects.

Minimal Example
---------------

Say you have a folder containing a single file ``notes.rst``.
To enable Esbonio's features in this file you would create a ``pyproject.toml`` file in the same folder containing something like the following.

.. code-block:: toml

   [tool.esbonio.sphinx]
   pythonCommand = ["uv", "run", "--no-project", "--with", "sphinx", "python"]
   buildCommand = ["sphinx-build", "-C", "-b", "html", ".", "${defaultBuildDir}"]

   [tool.esbonio.sphinx.configOverrides]
   root_doc = "notes"


The ``pythonCommand`` setting instructs Esbonio how to launch the background process with the correct version of Python.
As you can see, tools like `uv <https://docs.astral.sh/uv/>`__ can be very useful in situations like this, but this can be any command that launches a Python interpreter, see :ref:`this guide <lsp-configure-sphinx-build-env>` for more examples.

.. tip::

   If you use the VSCode extension, (or any client that sets the ``esbonio.sphinx.fallbackEnv``) option, then you can omit the ``pythonCommand`` setting and have ``esbonio`` use the default environment provided by your editor.

The ``buildCommand`` setting instructs Esbonio how to invoke Sphinx.
**The most important option here is** ``-C`` as this prevents Sphinx from looking for the ``conf.py`` file you see in a typical project.
See :ref:`this guide <lsp-configure-sphinx-build-cmd>` for more examples.

Finally, by default, Sphinx looks for a file called ``index.rst``.
Using the ``tool.esbonio.sphinx.configOverrides`` section we can override the ``root_doc`` setting to point it ``notes.rst`` instead.

Markdown Example
----------------

If you prefer, you can use Esbonio with your markdown files - assuming you have the necessary dependencies available.

.. code-block:: toml

   [tool.esbonio.sphinx]
   buildCommand = ["sphinx-build", "-C", "-b", "html", ".", "${defaultBuildDir}"]
   pythonCommand = [
       "uv", "run", "--no-project",
       "--with", "sphinx",
       "--with", "myst-parser",
       "python"
   ]

   [tool.esbonio.sphinx.configOverrides]
   extensions = [ "myst_parser" ]
   root_doc = "notes"

Third-Party Extensions, Themes and Options
------------------------------------------

As you might be able to guess from the previous two examples, you can provide many of the settings you would find in a ``conf.py`` file direct in your ``pyproject.toml`` file!

.. code-block:: toml

   [tool.esbonio.sphinx]
   buildCommand = ["sphinx-build", "-C", "-b", "html", ".", "${defaultBuildDir}"]
   pythonCommand = [
       "uv", "run", "--no-project",
       "--with", "sphinx",
       "--with", "myst-parser",
       "--with", "sphinx-design",
       "--with", "furo",
       "python"
   ]


   [tool.esbonio.sphinx.configOverrides]
   extensions = [
       "myst_parser",
       "sphinx.ext.intersphinx",
       "sphinx_design",
   ]
   project = "My Notes"
   root_doc = "notes"

   html_theme = "furo"
   html_title = "Notes"

   intersphinx_mapping.python = [
       "https://docs.python.org/3/",
       # Need to explicitly provide the objects.inv URL here as TOML does not
       # have an equivalent for `None`
       "https://docs.python.org/3/objects.inv"
   ]

Obviously beyond a certain point, you are better off just creating a ``conf.py`` file but this might be useful for providing reproducable examples when submitting bug reports!
