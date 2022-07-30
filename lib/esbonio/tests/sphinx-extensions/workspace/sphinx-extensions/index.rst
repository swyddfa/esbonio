.. Defaults documentation master file, created by
   sphinx-quickstart on Wed Dec  2 22:54:25 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _welcome:

Welcome to Defaults's documentation!
====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   diagnostics
   theorems/index
   glossary

Setup
=====

In order to run the program you need a few environment variables set.

.. envvar:: ANGLE_UNIT

   Use this environment variable to set the unit used when describing angles. Valid
   values are ``degress``, ``radians`` or ``gradians``.

.. envvar:: PRECISION

   Use this to set the level of precision used when manipulating floating point numbers.
   Its value is an integer which represents the number of decimal places to use, default
   value is ``2``
