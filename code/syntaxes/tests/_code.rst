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