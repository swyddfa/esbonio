-- SYNTAX TEST "source.rst" "directives"
-- In this file we use '-' as the comment character as vscode-tmgrammar-test
-- gets confused between comments and directives.

.. include:: somefile.rst
-- ^^^^^^^ entity.name.function

.. toctree::
   :glob:
--  ^^^^ storage.modifier

.. cpp:function:: x.y.z
-- ^^^ storage.type.namespace
--     ^^^^^^^^ entity.name.function