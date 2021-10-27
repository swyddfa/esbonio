-- SYNTAX TEST "source.rst" "code"
-- In this file we use '-' as the comment character as vscode-tmgrammar-test
-- gets confused between comments and directives.

.. code-block:: c

   int main(void) {}
-- ^^^^^^^^^^^^^^^^^ source.c

.. code-block:: c
   :linenos:
--  ^^^^^^^ storage.modifier

   int main(void) {}

.. code-block:: c
   :linenos:

   int main(void) {}
-- ^^^^^^^^^^^^^^^^^ source.c

.. code-block:: cpp

   std::cout << "Hello, world" << std::endl;
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.cpp

.. code-block:: cpp
   :emphasize-lines: 1
--  ^^^^^^^^^^^^^^^ storage.modifier

   std::cout << "Hello, world" << std::endl;

.. code-block:: cpp
   :emphasize-lines: 1

   std::cout << "Hello, world" << std::endl;
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.cpp

.. code-block:: css

   p {width: 50%}
-- ^^^^^^^^^^^^^^ source.css

.. code-block:: css
   :linenos:
--  ^^^^^^^ storage.modifier

   p {width: 50%}

.. code-block:: css
   :linenos:

   p {width: 50%}
-- ^^^^^^^^^^^^^^ source.css

.. code-block:: html

   <p class="example">html</p>
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^ text.html.derivative

.. code-block:: html
   :linenos:
--  ^^^^^^^ storage.modifier

   <p class="example">html</p>

.. code-block:: html
   :linenos:

   <p class="example">html</p>
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^ text.html.derivative

.. code-block:: javascript

   import { join } from 'path';
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.js

.. code-block:: javascript
   :linenos:
--  ^^^^^^^ storage.modifier

   import { join } from 'path';

.. code-block:: javascript
   :linenos:

   import { join } from 'path';
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.js

.. code-block:: ini

   [section]
   name = value
-- ^^^^^^^^^^^^ string

.. code-block:: ini
   :linenos:
--  ^^^^^^^ storage.modifier

   [section]
   name = value
-- ^^^^^^^^^^^^ string

.. code-block:: ini
   :linenos:

   [section]
   name = value
-- ^^^^^^^^^^^^ string

.. code-block:: js

   console.log("Hi there!")
-- ^^^^^^^^^^^^^^^^^^^^^^^^ source.js

.. code-block:: js
   :linenos:
--  ^^^^^^^ storage.modifier

   console.log("Hi there!")

.. code-block:: js
   :linenos:

   console.log("Hi there!")
-- ^^^^^^^^^^^^^^^^^^^^^^^^ source.js

.. code-block:: json

   {"example": "json"}
-- ^^^^^^^^^^^^^^^^^^^ source.json

.. code-block:: json
   :linenos:
--  ^^^^^^^ storage.modifier

   {"example": "json"}

.. code-block:: json
   :linenos:

   {"example": "json"}
-- ^^^^^^^^^^^^^^^^^^^ source.json

.. code-block:: python

   print("Hi there!")
-- ^^^^^^^^^^^^^^^^^^ source.python

.. code-block:: python
   :linenos:
   :caption: look at that!
--  ^^^^^^^ storage.modifier

   print("Hi there!")
-- ^^^^^^^^^^^^^^^^^^ source.python

.. code-block:: python
   :linenos:

   print("Hi there!")
-- ^^^^^^^^^^^^^^^^^^ source.python

.. code-block:: ts

   function test(a: number, b: string) {}
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.ts

.. code-block:: ts
   :caption:
--  ^^^^^^^ storage.modifier

   function test(a: number, b: string) {}

.. code-block:: ts
   :caption:

   function test(a: number, b: string) {}
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.ts

.. code-block:: typescript

   function test(a: number, b: string) {}
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.ts

.. code-block:: typescript
   :linenos:
--  ^^^^^^^ storage.modifier

   function test(a: number, b: string) {}

.. code-block:: typescript
   :linenos:

   function test(a: number, b: string) {}
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.ts

.. code-block:: yaml

   example: yaml
-- ^^^^^^^^^^^^^^ source.yaml

.. code-block:: yaml
   :linenos:
--  ^^^^^^^ storage.modifier

   example: yaml

.. code-block:: yaml
   :linenos:

   example: yaml
-- ^^^^^^^^^^^^^^ source.yaml

.. doctest::

   >>> print("Hi there")
-- ^^^^^^^^^^^^^^^^^^^^^ source.python

.. doctest::
   :hide:
--  ^^^^ storage.modifier

   >>> print("Hi there")

.. doctest::
   :hide:

   >>> print("Hi there")
-- ^^^^^^^^^^^^^^^^^^^^^ source.python

.. testcode::

   print("Hi there")
-- ^^^^^^^^^^^^^^^^^ source.python

.. testcode::
   :hide:
--  ^^^^ storage.modifier

   print("Hi there")

.. testcode::
   :hide:

   print("Hi there")
-- ^^^^^^^^^^^^^^^^^ source.python

.. testsetup::

   import matplotlib.pyplot as plt
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.python

.. testsetup::
   :skipif:
--  ^^^^^^ storage.modifier

   import matplotlib.pyplot as plt

.. testsetup::
   :skipif:

   import matplotlib.pyplot as plt
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ source.python

.. testcleanup::

   outputs.remove()
-- ^^^^^^^^^^^^^^^^ source.python

.. testcleanup::
   :skipif:
--  ^^^^^^ storage.modifier

   outputs.remove()

.. testcleanup::
   :skipif:

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
