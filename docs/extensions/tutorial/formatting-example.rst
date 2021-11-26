:tutorial: notebook

Formatting Example
==================

This tutorial demonstrates how different features of your reStructuredText document are
rendered in the exported notebook.

Basic Formatting
----------------

Your explanations are converted into markdown and included as markdown cells within the
exported notebook.

**Bold**, *Italics*, ``inline code``, and math (e.g. :math:`\sqrt{b^2 - 4ac}`) work as you would expect.

More exotic inline markup like :guilabel:`GUI Labels` and :kbd:`Key bindings` are simply rendered
as inline code.

reStructuredText style `inline hyperlinks <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html?highlight=raw%3A%3A#hyperlinks>`_
are converted to their markdown equivalents. `Named hyperlinks`_ are also converted into inline
markdown links.

.. _named hyperlinks: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html?highlight=raw%3A%3A#hyperlinks

.. reStructuredText comments are simply ignored.

Lists
-----

Unordered Lists
^^^^^^^^^^^^^^^

aka. bullet point lists.

- Item A
- Some items may be larger than others.
  There could be multiple lines of text

  There could even be content spread over multiple paragraphs

- Some items

  - may include
  - nested lists

Ordered Lists
^^^^^^^^^^^^^

Typically used to describe a sequence of steps.

#. Step one
#. Step two.
   This one is more involved

   And requires more explanation

#. Step three

Definition Lists
^^^^^^^^^^^^^^^^

Definition lists don't have an obvious counterpart in markdown. Currently they are
transformed into a normal bulleted list, with the ``term`` being defined rendered as
inline code.

print
  Function to display text in the console.

  Accepts a number of different options that control the formatting.

open
  Function that can be used to open files.

Blocks
------

Quoted Blocks
^^^^^^^^^^^^^

    To be or not to be.

Quoted blocks are translated into their markdown equivalents

Line Blocks
^^^^^^^^^^^

Line blocks are translated into a fenced block

| Abc
| def ghi
| zxy

Literal Blocks
^^^^^^^^^^^^^^

A literal block is by default treated as python code and rendered as an executable
cell in the exported notebook. To change how these blocks are handled, see the
:rst:dir:`sphinx:highlight` directive and  :confval:`sphinx:highlight_language`
configuration option for more details::

   sum([x*x for x in range(10)])

Literal blocks that do not contain python code, will instead be rendered as fenced
blocks inside a markdown cell

.. highlight:: none

::

   this cell
      does not
         contain code

Currently this also applies to any block that might otherwise be executable within a
notebook given the appropriate kernel.

.. highlight:: js

::

   [1,2,3].map(n => n*n)
          .reduce((m, n) => m+n, 0)

Code Blocks
^^^^^^^^^^^

Code blocks follow the same rules as outlined above for literal blocks.

.. code-block:: python

   import string
   {c: ord(c) for c in string.ascii_letters}

.. code-block:: none

   this block
     contains
   no code

.. code-block:: js

   console.log("Hello, World!")

Images
------

.. image:: /images/vscode-screenshot.png
   :align: center

Admonitions
-----------

Since there is no direct counterpart to admonitions in markdown, the extension does its
best to approximate them using quoted blocks. Below are some example admonitions.

Attention
^^^^^^^^^

.. attention::

   Be sure to save your changes before closing.

Caution
^^^^^^^

.. caution::

   This feature is a work in progress, be sure to back up your data.

Danger
^^^^^^

.. danger::

   Migrating from v1 to v3 directly is not supported! You may experience
   data loss!

Error
^^^^^

.. error::

   Something happended that prevented the configurator from configurating
   the thing. Pray that this message might mean something to someone because
   I can't help you.

   .. code-block:: none

      +----------------------------------------------------------------+
      |                          !Error!                               |
      |                                                                |
      | Configurator sprocket was misaligned to the flange, revert the |
      | combobulator to base level inductance before trying to dis     |
      | the belated combo.                                             |
      +----------------------------------------------------------------+

Hint
^^^^

.. hint::

   Try turining it off and on again.

Important
^^^^^^^^^

.. important::

   Switch on before use.

Note
^^^^

.. note::

   There are some situations where this may not apply.

Tip
^^^

.. tip::

   For best results:

   - try on a Thursday afternoon.
   - do not submerge in water
   - never throw it out a window.

Warning
^^^^^^^

.. warning::

   This feature will be removed in future versions.

   Be sure to check the release notes before upgrading.
