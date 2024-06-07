Python Domain
=============

The Python domain provides a set of roles and directives for documenting Python code.
Consider the following::

  import re

  DEFAULT_PATTERN = re.compile(r"\b\w+\b")


  class NoMatchesError(RuntimeError):
      pass

  class PatternCounter:
      def __init__(self, pattern=None):
          self._pattern = pattern or DEFAULT_PATTERN

      @classmethod
      def fromstr(cls, pattern: str):
          return cls(re.compile(pattern))

      @property
      def pattern(self):
          return self._pattern

      def count(self, text: str) -> int:
          if (num_matches := len(self.pattern.findall(text))) == 0:
              raise NoMatchesError()

          return num_matches

  def count_numbers(text: str):
      pattern = re.compile(r"\b\d+\b")
      counter = PatternCounter(pattern)

      return counter.count(text)

You could use the Python domain as follows to document it

.. module:: counters.pattern

.. exception:: NoMatchesError(RuntimeError)

   Raised when the :class:`PatternCounter` class does not find any matches.

.. data:: DEFAULT_PATTERN
   :type: re.Pattern
   :value: re.compile(r"\b\w+\b")

   The default pattern used when creating an instance of :class:`PatternCounter` with no arguments.

.. class:: PatternCounter(pattern=None)

   This counter implementation counts the occurances of the given regular expression in a string.
   If ``pattern`` is ``None``, :data:`DEFAULT_PATTERN` will be used.

   .. classmethod:: fromstr(cls, pattern: str)

      Helper for creating a ``PatternCounter`` instance from a string

   .. property:: pattern
      :type: re.Pattern

      The pattern used by this instance

   .. method:: count(self, text: str) -> int

      Return the number of matches found in the given ``text``.
      Raises a :exc:`NoMatchesError` if no matches can be found.

.. function:: count_numbers(text: str) -> int

   Helper function for counting the amount of numbers contained in the given ``text``.
