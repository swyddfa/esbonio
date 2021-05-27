-- SYNTAX TEST "source.rst" "links"

This line has an `inline <https://github.com>`_ link
--               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.link.rst
--                                            ^ keyword.operator
--               ^^^^^^^                     ^ string
--                       ^^^^^^^^^^^^^^^^^^^^ constant.other.url

There are `one <a.html>`_ or `two <b.html>`_ ways to approach this
--        ^^^^^^^^^^^^^^^ meta.link.rst
--                      ^ keyword.operator
--        ^^^^^        ^ string
--             ^^^^^^^^ constant.other.url
--                       ^^^^ -meta.link.url
--                           ^^^^^^^^^^^^^^^ meta.link.rst
--                                         ^ keyword.operator
--                           ^^^^^        ^ string
--                                ^^^^^^^^ constant.other.url

This is a `named`_ link
--        ^^^^^^^^ meta.reference.link.rst
--        ^^^^^^^ variable.other.label

Here is a `named`_ link, followed by `another`_
--        ^^^^^^^^ meta.reference.link.rst
--        ^^^^^^^ variable.other.label
--                                   ^^^^^^^^^^ meta.reference.link.rst
--                                   ^^^^^^^^^ variable.other.label
--                ^^^^^^^^^^^^^^^^^^^ -meta.reference.link.rst
--                ^^^^^^^^^^^^^^^^^^^ -variable.other.label
.. _named: https://example.com
-- ^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.definition.link.rst
-- <- keyword.operator
--  ^^^^^ variable.other.label
-- ^     ^ keyword.operator
--         ^^^^^^^^^^^^^^^^^^^ constant.other.url
