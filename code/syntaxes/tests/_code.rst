-- SYNTAX TEST "source.rst" "code"
-- In this file we use '-' as the comment character as vscode-tmgrammar-test
-- gets confused between comments and directives.

.. code-block:: css

   p {width: 50%}
-- ^^^^^^^^^^^^^^ source.css

.. code-block:: html

   <p class="example">html</p>
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^ text.html.derivative

.. code-block:: json

   {"example": "json"}
-- ^^^^^^^^^^^^^^^^^^^ source.json

.. code-block:: python

   print("Hi there!")
-- ^^^^^^^^^^^^^^^^^^ source.python

.. code-block:: yaml

   example: yaml
-- ^^^^^^^^^^^^^^ source.yaml

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

The following should be highlighted as a literal block::

   I am a literal block
-- ^^^^^^^^^^^^^^^^^^^^ meta.literal-block.rst string

Literal blocks can also span multiple paragraphs::

   This is the first paragraph.

   And here is the second.
-- ^^^^^^^^^^^^^^^^^^^^ meta.literal-block.rst string

A literal block should then end once the text is de-dented::

   Here is my literal text

But then this should be a regular paragraph again.
-- <--------------------- -string -meta.literal-block.rst

   However there may be situations where the literal block starts
   from an indented position::

      And the grammar should still be able to highlight the indented parts
--    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  meta.literal-block.rst string

   But once we get::

      to a dedented, but still indented block

   the highlighting should return to normal
-- ^^^^^^^^^^^^^^^^^^^^^^^ -string
