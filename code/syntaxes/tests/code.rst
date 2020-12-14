-- SYNTAX TEST "source.rst" "code"
-- In this file we use '-' as the comment character as vscode-tmgrammar-test
-- gets confused between comments and directives.

.. code-block:: python

   print("Hi there!")
-- ^^^^^^^^^^^^^^^^^^ source.python

.. doctest::

   >>> print("Hi there")
-- ^^^^^^^^^^^^^^^^^^^^^ source.python

.. testcode::

   print("Hi there")
-- ^^^^^^^^^^^^^^^^^ source.python

.. testsetup::

   import matplotlib.pyplot as plt
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.python

.. testcleanup::

   outputs.remove()
-- ^^^^^^^^^^^^^^^^ source.python