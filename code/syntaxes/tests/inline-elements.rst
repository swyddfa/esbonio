.. SYNTAX TEST "source.rst" "inline elements"

This line has **bold** text
..            ^^^^^^^^ markup.bold

**Note** this should be bold
.. <-------- markup.bold

Here are **multiple** bold **texts** on one line
..       ^^^^^^^^^^^^ markup.bold
..                   ^^^^^^ -markup.bold
..                         ^^^^^^^^^ markup.bold

This line has *italic* text
..            ^^^^^^^^ markup.italic

*Note* this should be italic
.. <------ markup.italic

Here are *multiple* italic *texts* on one line
..       ^^^^^^^^^^ markup.italic
..                 ^^^^^^^^ -markup.italic
..                         ^^^^^^^ markup.italic

This line has ``inline`` code
..            ^^^^^^^^^^ string

Here is ``some`` inline ``code``
..      ^^^^^^^^ string
..              ^^^^^^^^ -string
..                      ^^^^^^^^ string

Here is ``some`thing`` tricky to ``handle``
..      ^^^^^^^^^^^^^^ string
..                    ^^^^^^^^^^^ -string
..                               ^^^^^^^^^^ string

This line contains a :ref:`reference_label`
..                   ^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
..                    ^^^ entity.name.function
..                         ^^^^^^^^^^^^^^^ support.constant

This line contains a :cpp:func:`reference_label`
..                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
..                        ^^^^ entity.name.function
..                    ^^^ storage.type.namespace
..                              ^^^^^^^^^^^^^^^ support.constant

This line contains a :ref:`reference <reference_label>`
..                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
..                    ^^^ entity.name.function
..                                   ^^^^^^^^^^^^^^^^^ support.constant

This line contains a :cpp:ref:`reference <reference_label>`
..                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
..                        ^^^ entity.name.function
..                    ^^^ storage.type.namespace
..                                       ^^^^^^^^^^^^^^^^^ support.constant

This line has an `inline <https://github.com>`_ link
..               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.link.rst
..                ^^^^^^ string
..                       ^^^^^^^^^^^^^^^^^^^^ support.constant