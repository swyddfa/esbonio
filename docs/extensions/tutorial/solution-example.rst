:tutorial: notebook

Solution Example
================

This is an example of how to write a tutorial that includes solutions

:func:`python:sorted` is a function that can be used to sort a list of items::

   nums = [5, 3, 8, -23, 11, 2, 1]
   sorted(nums)

The ``reverse`` flag can be used to sort the items in descending order::

   sorted(nums, reverse=True)

Of course this function can be used to sort more than just numbers::

   fruit = ["cherry", "apple", "kiwi", "orange", "strawberry", "banana"]
   sorted(fruit)

It's even possible to provide a custom function to specify the criteria by which
you want the items sorted. For example, instead of sorting fruit alphabetically,
we can sort them by the number of characters in their name::

   sorted(fruit, key=len)

Exercises
---------

Test your understanding with the following excercises

Exercise 1
^^^^^^^^^^

Sort the list of fruit, by the number of characters in their name in descending
order

.. solution::

   ::

      sorted(fruit, key=len, reverse=True)

Exercise 2
^^^^^^^^^^

Sort the list of fruit, by the number of vowels in their name in ascending order

.. solution::

   To solve this, we need to write a function that takes a string and returns the number
   of vowels in that string. We can then pass it to the ``key`` parameter of the ``sorted``
   function to set the sort criteria.

   We can use a list comprehension to get a list of the vowel characters in a string
   ``[c for c in 'string' if c in 'aeiou']``. From there we can use ``len`` to count
   them and we get our solution::

      def num_vowels(name: str) -> int:
          return len([c for c in name if c in 'aeiou'])

      sorted(fruit, key=num_vowels)

Exercise 3
^^^^^^^^^^

Given the following list of tuples, representing fruit and their corresponding
cost, sort them from most to least expensive::

   fruit = [("cherry", 0.2), ("apple", 1.2), ("kiwi", 2.5), ("orange", 2), ("strawberry", 0.5), ("banana", 1.8)]

.. solution::

   ::

      def get_price(item: tuple) -> int:
          return item[1]

      sorted(fruit, key=get_price, reverse=True)
