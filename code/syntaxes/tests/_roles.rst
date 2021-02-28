-- SYNTAX TEST "source.rst" "roles"

This line contains a :ref:`reference_label`
--                   ^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
--                    ^^^ entity.name.function
--                         ^^^^^^^^^^^^^^^ support.constant

This line contains a :cpp:func:`reference_label`
--                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
--                        ^^^^ entity.name.function
--                    ^^^ storage.type.namespace
--                              ^^^^^^^^^^^^^^^ support.constant

This line contains a :ref:`reference <reference_label>`
--                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
--                    ^^^ entity.name.function
--                                   ^^^^^^^^^^^^^^^^^ support.constant

This line contains a :cpp:ref:`reference <reference_label>`
--                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.role.rst
--                        ^^^ entity.name.function
--                    ^^^ storage.type.namespace
--                                       ^^^^^^^^^^^^^^^^^ support.constant
