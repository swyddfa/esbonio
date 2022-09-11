.. _pythagoras_theorem:

Pythagoras' Theorem
===================

Pythagoras' Theorem describes the `relationship` between the length of the
sides of a right angled triangle.

.. include:: ../math.rst

.. include:: /math.rst

.. _the-implementation:

Implementation
--------------

This project provides some functions which use Pythagoras' Theorem to calculate the
length of a missing side of a right angled triangle when the other two are known.

.. module:: pythagoras

.. currentmodule:: pythagoras

.. data:: PI

   The value of the constant pi.

.. data:: UNKNOWN

   Used to represent an unknown value.

.. class:: Triangle(a: float, b: float, c: float)

   Represents a triangle

   .. attribute:: a

      The length of the side labelled ``a``

   .. attribute:: b

      The length of the side labelled ``b```

   .. attribute:: c

      The length of the side labelled ``c``

   .. method:: is_right_angled() -> bool

      :return: :code:`True` if the triangle is right angled.
      :rtype: bool

.. function:: calc_hypotenuse(a: float, b: float) -> float

   Calculates the length of the hypotenuse of a right angled triangle.

   :param float a: The length of the side labelled ``a``
   :param float b: The length of the side labelled ``b``
   :return: Then length of the side ``c`` (the triangle's hypotenuse)
   :rtype: float

.. function:: calc_side(c: float, b: float) -> float

   Calculates the length of a side of a right angled triangle.

   :param float c: The length of the side labelled ``c`` (the triangle's hypotenuse)
   :param float b: The length of the side labelled ``b``
   :return: Then length of the side ``a``
   :rtype: float

.. |rhs| replace:: right hand side
