-- SYNTAX TEST "source.rst" "links"

This line has an `inline <https://github.com>`_ link
--               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.link.rst
--                                            ^ keyword.operator
--               ^^^^^^^                     ^ string
--                       ^^^^^^^^^^^^^^^^^^^^ constant.other.url

This is a `named`_ link
--        ^^^^^^^^ meta.reference.link.rst
--        ^^^^^^^ variable.other.label

.. _named: https://example.com
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition.link.rst
-- <- keyword.operator
--  ^^^^^ variable.other.label
-- ^     ^ keyword.operator
--         ^^^^^^^^^^^^^^^^^^^ constant.other.url