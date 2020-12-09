Tutorial
========

The tutorial extension can be enabled by including :code:`esbonio.tutorial` in
your extensions list

.. code-block:: python

   extensions = [
      "esbonio.tutorial",
   ]

Has the ability to write tutorials and export them as Jupyter notebooks. These
can then made available online through cli commands or a notebook hosting
service like Binder.


Solutions
---------

If you want your tutorials to include exercises

**Example**

.. code-block:: rst

   .. solution::

      .. code-block:: python

         x = 1 + 3
         print(x)

.. solution::

   .. code-block:: python

      x = 1 + 3
      print(x)
