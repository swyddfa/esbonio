Directives
==========

The language server has extensive support for directives.

Completion
----------

The most obvious feature is the completion suggestions, try inserting a ``.. note::`` directive on the next line

.. Add your note here...

Notice how VSCode automatically presented you with a list of all the directives you can use in this Sphinx project?

Arguments
^^^^^^^^^

While directive names Just Work\ :sup:`TM`, Esbonio is only able to offer suggestions for specific argument types.
By default Esbonio can provide suggestions for

**Filepaths**

Completing filepath arguments is supported for the following directives

- `figure <https://docutils.sourceforge.io/docs/ref/rst/directives.html#figure>`__
- `image <https://docutils.sourceforge.io/docs/ref/rst/directives.html#image>`__
- `include <https://docutils.sourceforge.io/docs/ref/rst/directives.html#image>`__
- :external+sphinx:rst:dir:`literalinclude`

.. Try using the `literalinclude` directive to insert the contents of this project's conf.py here...

**Pygments Lexers**

Sphinx uses the `pygments <https://pygments.org/>`__ library for its syntax highlighting, Esbonio will offer the names of available lexers as suggestions for the following directives.

- :external+sphinx:rst:dir:`code`
- :external+sphinx:rst:dir:`code-block`
- :external+sphinx:rst:dir:`highlight`
- :external+sphinx:rst:dir:`sourcecode`

.. Try inserting a code block on the next line...
