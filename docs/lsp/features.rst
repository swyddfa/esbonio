Features
========

This page contains a quick overview of the features offered by the Language
Server

Completion
----------

The language server can offer auto complete suggestions in a variety of contexts

.. figure:: ../../resources/images/completion-demo.gif
   :align: center

Diagnostics
-----------

The language server is able to catch some of the errors Sphinx outputs while
building and publish them as diagnostic messages

.. figure:: ../../resources/images/diagnostic-sphinx-errors-demo.png
   :align: center

   Example diagnostic messages from Sphinx

Goto Definition
---------------

The language server can look up the definition of certain role targets.
Currently this is limited to just the ``:ref:`` and ``:doc:`` roles.

.. figure:: ../../resources/images/definition-demo.gif
   :align: center
