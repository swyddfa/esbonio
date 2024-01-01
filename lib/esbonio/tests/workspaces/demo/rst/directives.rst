Directives
==========

The language server has extensive support for directives.

Completion
----------

The most obvious feature is the completion suggestions, try inserting a ``.. note::`` directive on the next line

.. Add your note here...

Notice how VSCode automatically presented you with a list of all the directives you can use in this Sphinx project?

Goto ...
--------

The language server also provides a number of "Goto" navigation commands.
On the ``.. note::`` directive you inserted above, try each of the following commands

- ``Implementation`` goto the source code that implements the selected directive
