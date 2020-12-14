-- SYNTAX TEST "source.rst" "directives"
-- In this file we use '-' as the comment character as vscode-tmgrammar-test
-- gets confused between comments and directives.

.. include:: somefile.rst
-- ^^^^^^^ entity.name.type

.. toctree::
   :glob:
--  ^^^^ entity.name.type
