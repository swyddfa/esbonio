.. SYNTAX TEST "source.rst" "inline elements"

This line has **bold** text
..            ^^^^^^^^ markup.bold

This line has *italic* text
..            ^^^^^^^^ markup.italic

This line has ``inline`` code
..            ^^^^^^^^^^ string

This line contains a :ref:`reference_label`
..                   ^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
..                    ^^^ keyword.letter
..                         ^^^^^^^^^^^^^^^ string

This line contains a :ref:`reference <reference_label>`
..                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
..                    ^^^ keyword.letter
..                                   ^^^^^^^^^^^^^^^^^ entity.name.function

This line has an `inline <https://github.com>`_ link
..               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.link.rst
..                ^^^^^^ string
..                       ^^^^^^^^^^^^^^^^^^^^ entity.name.function