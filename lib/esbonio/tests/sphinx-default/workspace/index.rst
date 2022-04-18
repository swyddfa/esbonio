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

   theorems/index
   definitions
   glossary

.. _setup-label:

Setup
=====

The program supports specifying configuration values through environment variables.

.. envvar:: ANGLE_UNIT

   Use this environment variable to set the unit used when describing angles. Valid
   values are ``degress``, ``radians`` or ``gradians``.

.. envvar:: PRECISION

   Use this to set the level of precision used when manipulating floating point numbers.
   Its value is an integer which represents the number of decimal places to use, default
   value is ``2``

Alternatively they can be set through command line options

.. program:: pythag

.. option:: -e, --exact

   Output results exactly (as a rational number)

.. option:: -u <unit>, --unit <unit>

   Specify the angle units to use can be one of ``degrees``, ``radians`` or ``gradians``.

.. option:: -p <prescision>, --precision <precision>

   The number of decimal places to use. This option is ignored when using :option:`pythag --exact`
