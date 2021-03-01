-- SYNTAX TEST "source.rst" "footnotes"

This line contains an explicitly numbered footnote reference [1]_
--                                                           ^^^^ meta.reference.footnote.rst
--                                                           ^ ^^ keyword.operator
--                                                            ^ meta.reference.footnote.explicit.rst variable.other.label

This line contains an anonymous auto numbered footnote reference [#]_
--                                                               ^^^^ meta.reference.footnote.rst
--                                                                ^ meta.reference.footnote.automatic.rst variable.other.label
--                                                               ^ ^^ keyword.operator

This line contains a labeled auto numbered footnote reference [#test]_
--                                                            ^^^^^^^^ meta.reference.footnote.rst
--                                                             ^^^^^ meta.reference.footnote.automatic.rst variable.other.label
--                                                            ^     ^^ keyword.operator

This line contains a citation reference [CIT2020]_
--                                      ^^^^^^^^^^ meta.reference.footnote.rst
--                                       ^^^^^^^ meta.reference.citation.rst variable.other.label
--                                      ^       ^^ keyword.operator

.. [1] Footnote definition
-- <------------------------- meta.definition.footnote.rst
-- ^ ^ keyword.operator
--  ^ variable.other.label

.. [#test] Another definiton
-- <--------------------------- meta.definition.footnote.rst
-- ^     ^ keyword.operator
--  ^^^^^ variable.other.label

.. [#test-multiline] This definition
   Is made up of multiple lines.
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition.footnote.rst
