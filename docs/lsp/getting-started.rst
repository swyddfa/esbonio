.. _lsp-getting-started:

Getting Started
===============

.. highlight:: none

This tutorial will guide you through the process of using the Esbonio language server with VSCode for the first time.
Even if VSCode is not your editor of choice, it is still recommended that you read through this guide as the concepts covered here will apply to other editors.

To follow along you will need either

- VSCode, Git and Python installed on your machine, or
- A GitHub account with access to `Codespaces <https://github.com/features/codespaces>`__

Initial Setup
-------------

This tutorial uses a `demo project <https://github.com/swyddfa/esbonio-demo>`__ to illustrate the features provided by Esbonio, so before we can begin we need to get this project setup on your machine.

The setup steps will be different depending on how you intend to follow along

- **VSCode**: Follow these steps if you are using a VSCode

- **VSCode + Dev Container**: Follow these steps if you are using VSCode, but want to use a `devcontainer <https://code.visualstudio.com/docs/devcontainers/containers>`__ for the project's environment.

- **Codespaces**: Follow these steps if you don't have VSCode or would prefer to use your browser.

.. tab-set::

   .. tab-item:: VSCode

      #. Open a terminal and clone the `demo repository <https://github.com/swyddfa/esbonio-demo>`__::

         $ git clone https://github.com/swyddfa/esbonio-demo

      #. Open the demo repository in VSCode::

         $ cd esbonio-demo && code .

      #. Open the :guilabel:`Extensions` sidebar (:kbd:`Ctrl+Shift+X`) and search for ``esbonio``.
         You should see the "Esbonio" extension at the top of the list, with an icon matching the logo you see on this documentation site.

      #. Instead of clicking the :guilabel:`Install` button, click the down arrow to the right of the :guilabel:`Install` text and pick the :guilabel:`Install Pre-Release` button.

   .. tab-item:: VSCode + Dev Container

      #. Open a terminal and clone the `demo repository <https://github.com/swyddfa/esbonio-demo>`__::

         $ git clone https://github.com/swyddfa/esbonio-demo

      #. Open the demo repository in VSCode::

         $ cd esbonio-demo && code .

      #. Assuming that you already have the `Dev Containers <https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers>`__ extension installed, you should be prompted to reopen the repository in a container.
         Alternatively, you can run the :guilabel:`Dev Containers: Reopen in Container` command through the command palette (:kbd:`Ctrl+Shift+P`)

      #. VSCode will automatically install the Esbonio extension as part of the container setup process.

   .. tab-item:: Codespaces

      #. Open the repository for the `demo project <https://github.com/swyddfa/esbonio-demo>`__ in your browser

      #. Sign in to GitHub if you have not done so already

      #. Click the green :guilabel:`<> Code` button

      #. Select the :guilabel:`Codespaces` tab in the popup dialog and click the green :guilabel:`Create codespace on main` button.

Open a Preview
--------------

.. |book-icon| image:: /images/book-icon.png
.. |globe-icon| image:: /images/globe-icon.png

By this point you should have the demo project open and the Esbonio extension installed.

#. Open the :guilabel:`Explorer` sidebar (:kbd:`Ctrl+Shift+E`) and click the ``index.rst`` file.

#. Open a preview of this file by either

   - Clicking the icon in header that looks like a book |book-icon|
   - Hitting the :kbd:`Ctrl+K V` keyboard shortcut
   - Running the :guilabel:`Esbonio: Preview Documentation in Split Window` command through the command palette (:kbd:`Ctrl+Shift+P`)

   After a few seconds the Esbonio extension will have built the documentation in the background and be showing the result in the new side window.

   .. admonition:: If you are using Codespaces...
      :class: warning

      Previews in Esbonio work by starting Python's built-in ``http.server`` in your project's build directory and are hosted on ``localhost:<port_number>`` - something that shouldn't normally work in a Codespace.
      Thankfully, GitHub will automatically expose local ports via your Codespace's URL e.g. ``https://codespace-name-q99gp466q62xwqw.github.dev:<port_number>/``

      Unfortunately, the browser will initially block Esbonio's preview pane from accessing this URL with a message like ``This content is blocked. Contact the site owner to fix the issue``.

      To fix this, we first need to open these Codespace URLs in a new tab

      #. If VSCode's bottom panel is not already open, open it with the :kbd:`Ctrl+J` shortcut.

      #. Select the :guilabel:`Ports` tab, you should see two URLs listed in a table.

      #. Click on the globe icon |globe-icon| next to each of the links to open them in a new tab

         - One of the links will take you to the documentation preview
         - The other will be an error message like ``Failed to open a WebSocket connection``. **This is expected, you can ignore this**

      #. Close both of the tabs and return to the Codespace

      #. Close the :guilabel:`Esbonio Preview` window and re-open it using one of the methods mentioned above.

#. Go back to the ``index.rst`` file and replace the ``.. Write a message here`` comment with ``Hello, World!``.

   Notice how after a few seconds the preview will update showing the result of the changes you made.

Fixing the Project Configuration
--------------------------------

By this point you may have noticed that there are some issues with this project.
Open VSCode's :guilabel:`Problems` tab (:kbd:`Ctrl+Shift+M`) and you will see a number of errors including

- Could not import extension sphinx_design (exception: No module named 'sphinx_design')
- No theme named 'furo' found (missing theme.toml?)
- Unknown directive type "grid"

Also if you compare your current preview to the `published version <https://demo.esbon.io/en/latest/>`__ of the demo documentation site, you can clearly see that Esbonio is not using the right theme!

This is because Esbonio is currently using a fallback environment which does not have access to all of the dependencies necessary to build the demo project.
While Esbonio is able to work around issues like this, it will work best when we are able to provide it access to a complete environment.

Let's create a virtual environment containing the required dependencies.

#. Open the Terminal (:kbd:`Ctrl+\``) and create a new virtual environment::

      $ python -m venv env

#. Activate the environment and install the demo project's dependencies::

      $ source env/bin/activate
      (env) $ python -m pip install -r requirements.txt

With the environment created, we now need to tell Esbonio to use it

#. Open the demo project's ``pyproject.toml`` file and add the following ``pythonCommand`` to the configuration

   .. code-block:: diff

        [tool.esbonio.sphinx]
        buildCommand = ["sphinx-build", "-M", "dirhtml", ".", "./_build"]
      + pythonCommand = ["${venv:env}"]

#. Save the file, Esbonio will detect the configuration change and automatically restart its background Sphinx process within the newly created environment

#. Remove the ``Hello, World!`` text you added in the previous section.
   The next time the preview refreshes you will see that Esbonio is now using the correct theme for this project and that the errors mentioned at the start of this section have been fixed!

Next Steps
----------

That's all you need to get started, you should now be able to make use of Esbonio in your own projects!

If you like, you can continue exploring the demo project to discover some of the other features Esbonio provides by clicking either

- the ``reStructuredText Demo`` card, or
- the ``MyST Demo`` card

in the preview pane.
Esbonio will open the corresponding section where you will be taken on a tour through the supported features of your selected syntax.

.. seealso::

   :ref:`lsp-configure-sphinx-build-env`
      Esbonio is able to work with more than just virtual environments, this guide will show you how to integrate it with other environment managers like poetry.

   :ref:`editor-integration`
      This section provides details on how to integrate Esbonio with other text editors
