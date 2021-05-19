-- SYNTAX TEST "source.rst" "comments"
-- In this file we use '-' as the comment character.

.. This line is a comment
-- <------ comment.line

.. A line that has the same indentation as a comment.
   Should also be a comment
-- ^^^^^^^^^^^^^^^^^^^^^^^^ comment.line

However... lines that contain ellipses should NOT be a comment.
--      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ -comment.line
