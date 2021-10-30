Tutorial
========

.. TODO: Future Ideas?

   These should probably converted to a GitHub issue at some point, but I'll
   just stick these here for now.

   - pytest integration?:

     In addition to providing model answers through the ``.. solution`` mechanism
     is there some way to define pytest tests that... pull functions out of the
     notebook environment and test them.

     Is there an extension geared towards just this use case i.e. automated marking
     of exercises? It would be good to reuse it and just expose an easy way to define
     exercises & tests through rst markup.

   - tutorial sections:

     I can imagine use cases where it might be nice to export just a section of a
     document as a tutorial. e.g. The getting started section of this page.

   - lsp support:

     Extend the LSP server to provide completion suggestions for code snippets written
     within the context of the tutorial.

   - alternate solutions:

     Sometimes it might be worth highlighting more than one way to approach a problem.
     Add the ability to specify multiple solutions within a single ``solution::`` block

         .. solution::
            :name: a

         .. alternate-solution::
            :for: a

     perhaps?

The tutorial extension's aim is to make it easy to export tutorials written as part of
your project's documentation to `Jupyter Notebooks`_ allowing the reader to follow along
in an interactive environment and further explore for themselves.

With online services such as `Binder`_ it's also possible to create fully interactive
online versions of your tutorials allowing the user to just try things out bypassing any
(potentially) complicated setup steps.

.. include:: _installation.rst

Getting Started
---------------

.. TODO:

   It might be fun to write a tutorial series that starts with the reader
   to build a simple Sphinx project that outputs the "Hello, world" example.
   The series could then go onto introduce each of the topics in the next
   section, Solutions, Translations etc.

   The trouble is whether that kind of tutorial actually fits in a Jupyter
   Notebook environment... Since it involves many files and cli commands,
   not sure if it would work online.

   Would we need/it be useful to have a mechanism where a tutorial writer
   can define checkpoints so the user knows if they have satisfied some criteria?

   e.g have a string ``esbonio.tutorial`` in a list called ``extensions`` in a
       file ``conf.py``

Ensure the extension is enabled by including :code:`esbonio.tutorial` in
your ``extensions`` list inside your project's ``conf.py``::

   extensions = [
      "esbonio.tutorial",
   ]

Tutorials are then written in the same way as you would write any other Sphinx based
documentation. Here is a simple "Hello, World!" Python tutorial.

.. literalinclude:: tutorial/hello-world.rst
   :language: rst

Note the only thing specific to this extension is the ``:tutorial: notebook``
:ref:`field list <sphinx:rst-field-lists>` at the start of the document to indicate
that this document is a tutorial.

This extension includes a :ref:`Sphinx Builder <sphinx:builders>` called ``tutorial``
that can then be used to export tutorials as ``*.ipynb`` files.

.. code-block:: console

   $ sphinx-build -b tutorial docs/ docs/_build/

Inside the ``docs/_build/tutorial`` directory, there should then be a ``hello-world.ipynb``
file containing the "Hello, World!" tutorial.

Writing Tutorials
-----------------

.. TODO:

   Resources
   ^^^^^^^^^

   Outline how additional resources like images are handled.

Solutions
^^^^^^^^^

If you want your tutorials to include exercises that the reader is meant to solve
the :rst:dir:`solution` directive can be used to insert solutions.

.. solution::

   .. code-block:: python

      x = 1 + 3
      print(x)

.. rst:directive:: solution

   Mark the content of the directive as being the solution to a tutorial exercise.

   **Example**

   .. code-block:: rst

      .. solution::

         .. code-block:: python

            x = 1 + 3
            print(x)

.. TODO:

   Translations
   ^^^^^^^^^^^^

   Outline how Sphinx's built-in translation system can be used to generate translated
   versions of tutorials.

Deploying Tutorials
-------------------

Once you've written and exported your tutorials, you probably want to make them
accessible to your users. Below are a few examples on ways you could distribute
them.

Local
^^^^^

Perhaps the most straightforward way is to package the tutorial alongside your
project. You could then provide a cli command that will automate the process 
of copying the tutorial into a location on the user's machine and starting up
a `Jupyter Lab`_ instance.

Packaging
"""""""""

.. tabbed:: setuptools

   The exported tutorial can be bundled in your Python package using the 
   `Data Files`_ support built into setuptools. This requires you to add the 
   following flag to your ``setup.cfg`` (or ``setup.py``) file

   .. code-block:: ini  

      [options]
      include_package_data = True

   Additionally you need to specify the folder(s) to include in your
   ``MANIFEST.in`` file (create one in the same folder as your ``setup.cfg``)
   file if you don't have one already). To use the ``esbonio-extensions``
   package as an example, you would add the following line

   .. code-block:: none

      recursive-include esbonio/tutorial/demo *
      

   If it's setup correctly, you should see your tutorial files listed in the 
   build output when you run

   .. code-block:: console
      :emphasize-lines: 6-12 

      $ python setup.py sdist bdist_wheel
      ...
      adding 'esbonio/tutorial/__init__.py'
      adding 'esbonio/tutorial/__main__.py'
      adding 'esbonio/tutorial/commands.py'
      adding 'esbonio/tutorial/demo/extensions/tutorial/formatting-example.ipynb'
      adding 'esbonio/tutorial/demo/extensions/tutorial/hello-world.ipynb'
      adding 'esbonio/tutorial/demo/extensions/tutorial/solution-example.ipynb'
      adding 'esbonio/tutorial/demo/resources/extensions/tutorial/formatting-example/vscode-screenshot.png'
      adding 'esbonio/tutorial/demo/resources/extensions/tutorial/solution-example/solution-example-soln-01.py'
      adding 'esbonio/tutorial/demo/resources/extensions/tutorial/solution-example/solution-example-soln-02.py'
      adding 'esbonio/tutorial/demo/resources/extensions/tutorial/solution-example/solution-example-soln-03.py'
      adding 'esbonio_extensions-0.0.2.dist-info/LICENSE'
      adding 'esbonio_extensions-0.0.2.dist-info/METADATA'
      adding 'esbonio_extensions-0.0.2.dist-info/WHEEL'
      adding 'esbonio_extensions-0.0.2.dist-info/top_level.txt'
      adding 'esbonio_extensions-0.0.2.dist-info/RECORD'

.. tabbed:: poetry 

   .. admonition:: TODO

      Figure this out

.. tabbed:: flit

   .. admonition:: TODO

      Figure this out

Binder
^^^^^^

Examples
--------

.. toctree::
   :glob:
   :maxdepth: 1

   tutorial/*


.. _Binder: https://mybinder.org/
.. _Data Files: https://setuptools.pypa.io/en/latest/userguide/datafiles.html
.. _Jupyter Lab: https://jupyterlab.readthedocs.io/en/stable/getting_started/overview.html
.. _Jupyter Notebooks: https://jupyter.org/
