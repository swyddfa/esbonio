"""This module implements the Sphinx agent.

It wraps a Sphinx application object, allowing the main language server process to
interact with it.

Whereas the language server originally had to be installed within the same Python
environment as Sphinx, the agent allows the server to run in a completely separate
Python environment and still gather the information it needs.

This is possible by taking advantage of the ``PYTHONPATH`` environment variable, using
it to expose *just this module* to the Python environment hosting Sphinx. To prevent
a potential clash of dependencies, this module is written with only what is available
in the stdlib and Sphinx itself.

Unfortunately, this does mean re-inventing some wheels, but hopefully what we gain in
portability makes it worth the trade off.
"""
