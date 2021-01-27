Features
========

This page contains a quick overview of the features offered by the Language
Server

Completion
----------

The Language Server can offer auto complete suggestions in a variety of contexts

Directives
^^^^^^^^^^

.. figure:: ../../resources/images/complete-directive-demo.gif
   :align: center

   Completing directive targets

.. note::

   Currently the Language Server makes a hardcoded assumption that your
   ``primary_domain`` is set to ``python`` and has no knowledge that other
   domains exist.

   Support for additional domains will come in a future release

Roles
^^^^^

.. figure:: ../../resources/images/complete-role-demo.gif
   :align: center

   Completing role names

.. note::

   Currently the Language Server makes a hardcoded assumption that your
   ``primary_domain`` is set to ``python`` and has no knowledge that other
   domains exist.

   Support for additional domains will come in a future release

Role Targets
^^^^^^^^^^^^

The lanuguage server is able to offer completions for the targets to a number of
different role types.

.. figure:: ../../resources/images/complete-role-target-demo.gif
   :align: center

   Completing role targets



Currently supported roles include

.. hlist::
   :columns: 3

   * :rst:role:`sphinx:doc`
   * :rst:role:`sphinx:envvar`
   * :rst:role:`sphinx:ref`
   * :rst:role:`sphinx:option`
   * :rst:role:`sphinx:py:attr`
   * :rst:role:`sphinx:py:class`
   * :rst:role:`sphinx:py:data`
   * :rst:role:`sphinx:py:exc`
   * :rst:role:`sphinx:py:func`
   * :rst:role:`sphinx:py:meth`
   * :rst:role:`sphinx:py:mod`
   * :rst:role:`sphinx:py:obj`
   * :rst:role:`sphinx:term`
   * :rst:role:`sphinx:token`
