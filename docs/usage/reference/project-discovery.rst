Sphinx Project Lookup
======================

Esbonio relies on Sphinx to provide the data that powers its :term:`LSP` features (e.g. completion suggestions).
Therefore, Esbonio needs to associate files with the correct Sphinx project instance.

This page outlines both how the language server makes this association as well as the process of creating new Sphinx instances on demand.

Configuration Scopes
--------------------

Sphinx project creation is closely tied to the concept of :ref:`configuration scopes <lsp-configuration-scopes>`.
For the purposes of project creation, you only need to know the following.

- A scope is a :term:`URI` within your workspace that configuration values can be associated with.

- Esbonio considers the root of each :term:`workspace folder` and each folder containing a ``pyproject.toml`` file to define a scope.

- **Only one Sphinx project per configuration scope is supported.**

Example Workspace
-----------------

.. highlight:: none

To illustrate the process, we will consider some example scenarios based on the following workspace structure::

   root-a
   ├── docs
   │   ├── about
   │   │   └── changelog.md
   │   ├── conf.py
   │   ├── index.rst
   │   └── usage
   │       ├── getting-started.rst
   │       └── reference.rst
   ├── myapp
   │   └── __init__.py
   ├── README.md
   └── pyproject.toml

   root-b
   ├── docs-one
   │   ├── conf.py
   │   └── index.rst
   ├── docs-two
   │   ├── conf.py
   |   └── src
   │       └── index.md
   └── libs
       ├── libone
       |   └── pyproject.toml
       └── libtwo
           └── pyproject.toml

Here we have a workspace composed of two workspace folders

- ``root-a`` which contains

  - A Python application ``myapp``
  - Associated documentation in the ``docs/`` folder.

- ``root-b`` which contains

  - Two Python libraries ``libone`` and ``libtwo``
  - Associated documentation as separate Sphinx projects ``docs-one`` and ``docs-two``

This structure results in the following configuration scopes being available.

- ``file:///path/to/root-a``
- ``file:///path/for/root-b``
- ``file:///path/for/root-b/lib/libone``
- ``file:///path/for/root-b/lib/libtwo``

Scenario One: ``root-a``
------------------------

First let's consider what happens when we open files in ``root-a``, where the project structure aligns well with Esbonio's default behaviour.

#. Let's open ``root-a/docs/about/changelog.md``

#. Esbonio determines the relevant configuration scope for this file by comparing the file's URI to the available scopes, selecting any that are a prefix of the file's URI.

   **File URI**: ``file:///path/to/root-a/docs/about/changelog.md``

   **Candidate Scope URIs**:

   - ✅ ``file:///path/to/root-a``
   - ❌ ``file:///path/for/root-b``
   - ❌ ``file:///path/for/root-b/lib/libone``
   - ❌ ``file:///path/for/root-b/lib/libtwo``

   In this scenario there is only one applicable scope, so it is selected by default.

#. Esbonio checks to see if there is already a Sphinx project associated with the selected configuration scope.
   As there is no project instance yet, one will be created.

#. In the absence of any configuration, the following defaults will be used.

   - **Working Directory**: The background Sphinx process will be started in the same folder as the configuration scope which in this case is ``/path/to/root-a``

   - **Source Directory**: Esbonio assumes that your Sphinx source directory is the same as the folder containing your ``conf.py`` file which it locates by searching upwards from the file.

     - ❌ ``file:///path/to/root-a/docs/about/conf.py``
     - ✅ ``file:///path/to/root-a/docs/conf.py``

     The source directory is taken relative to the working directory: ``docs/`` in this example.

   - **Build Directory**: Esbonio selects a default build directory with the help of `platformdirs <https://github.com/tox-dev/platformdirs>`__

     ``${CACHE_DIR}/${PROJECT_HASH}``

     where:

     - ``CACHE_DIR = platformdirs.user_cache_dir(appname="esbonio", appauthor="swyddfa")``
     - ``PROJECT_HASH = md5(<Source Directory>)``

     So in this example, the build directory might look something like ``/home/user/.cache/esbonio/f238f5fc3895aa1fcd4a5c185b2d0e85``

#. Using the configuration derived in the previous step, Esbonio constructs  set of ``sphinx-build`` arguments and launches a background Sphinx process **roughly equivalent** to::

     /path/to/root-a $ sphinx-build -M dirhtml docs/ /home/user/.cache/esbonio/f238f5fc3895aa1fcd4a5c185b2d0e85

   In the absence of any configuration, Esbonio launches the command within the same Python environment that itself is running in.

   .. important::

      Esbonio **does not** run the ``sphinx-build`` command.
      Instead it uses a custom wrapper program defined in ``esbonio.sphinx_agent`` that allows the Sphinx process to be controlled remotely by the main ``esbonio`` server.

   .. note::

      Language clients, such as the VSCode extension, can override the default Python environment when launching the server.
      This is how the extension's fallback environment is implemented. (Link to more details will appear here once they are written.)

#. When subsequent files within the project are opened, the existing background process will be selected.

Scenario Two: ``root-b``
------------------------

Now let's consider the slightly more complicated structure in ``root-b`` where Esbonio is going to require some assistance.

#. First, let's open ``root-b/docs-one/index.rst``.

   The same process outlined in the previous scenario will be followed resulting in:

   **Scope URI:** ``file:///path/for/root-b``

   **sphinx-build equivalent**::

     /path/for/root-b $ sphinx-build -M dirhtml docs-one /home/user/.cache/esbonio/b35fc2dfe910adc01fc5775e70a17008

#. Now let's consider what happens when we open ``root-b/docs-two/index.md``.

   Esbonio follows the process outlined in the previous section and finds the configuration scope applicable to this file is ``file:///path/for/root-b``.
   Since there is already a Sphinx process associated with this scope, it's going to try and reuse it.

#. However once a Sphinx process has been established, Esbonio can determine which files are used during a Sphinx build.
   It will be able to see the ``root-b/docs-two/index.md`` is not a part of the project created in step 1 and ignore it.

**The fix**

In order for Esbonio to recognise the second project, we need a configuration scope specific enough to only contain the ``docs-two/`` folder.
This can be done in one of two ways:

- Open just the ``/path/for/root-b/docs-two`` folder in your editor.
- Add a ``pyproject.toml`` file to the root of the ``docs-two/`` folder.
