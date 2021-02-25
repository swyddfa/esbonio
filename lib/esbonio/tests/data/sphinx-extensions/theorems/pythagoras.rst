.. _pythagoras_theorem:

Pythagoras' Theorem
===================

Pythagoras' Theorem describes the relationship between the length of the
sides of a right angled triangle.

Implementation
--------------

This project provides some functions which use Pythagoras' Theorem to calculate the
length of a missing side of a right angled triangle when the other two are known.

.. py:module:: pythagoras

.. py:currentmodule:: pythagoras

.. py:data:: PI

   The value of the constant pi.

.. py:data:: UNKNOWN

   Used to represent an unknown value.

.. py:class:: Triangle(a: float, b: float, c: float)

   Represents a triangle

   .. py:attribute:: a

      The length of the side labelled ``a``

   .. py:attribute:: b

      The length of the side labelled ``b``

   .. py:attribute:: c

      The length of the side labelled ``c``

   .. py:method:: is_right_angled() -> bool

      :return: :code:`True` if the triangle is right angled.
      :rtype: bool

.. py:function:: calc_hypotenuse(a: float, b: float) -> float

   Calculates the length of the hypotenuse of a right angled triangle.

   :param float a: The length of the side labelled ``a``
   :param float b: The length of the side labelled ``b``
   :return: Then length of the side ``c`` (the triangle's hypotenuse)
   :rtype: float

.. py:function:: calc_side(c: float, b: float) -> float

   Calculates the length of a side of a right angled triangle.

   :param float c: The length of the side labelled ``c`` (the triangle's hypotenuse)
   :param float b: The length of the side labelled ``b``
   :return: Then length of the side ``a``
   :rtype: float
