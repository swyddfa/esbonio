Preview Implementation
======================

This page gives an overview of how the preview feature in ``esbonio`` is implemented.


.. figure:: /images/preview-architecture.svg
   :align: center

   Architecture of the preview feature

The diagram above shows the main components involved in implementing the preview feature.

- On the left we have the user's text editor of choice e.g. VSCode, Vim, Emacs etc
- On the right we have the webview used to show the preview of the user's documentation.
  In the case of VSCode this is probably a built-in webview, but for other editors it's most likely to be a web browser.
- In the center there is the ``esbonio`` language server itself with two additional components.

  - A HTTP server, used to serve files out of the build directory
  - A WebSocket server, used for communication between the language server and the webview.

Typical Workflow
----------------

At a high level the typical interaction between the components may look something like the following.

#. The user previews a given file in their editor.
#. If it hasn't done so already, the language server creates a WebSocket server to listen for connections from a webview.
#. If it hasn't done so already, the language server creates a HTTP server and configures it to serve content out of the relevant build directory.
#. The server informs the editor the url at which the preview server can be found and the webview is opened.
#. Once the page loads in the webview, the WebSocket client embedded in the page connects to the WebSocket server running in the Language Server.
   Using the Language Server as an intermediary, it's now possible for the editor and webview to communicate with each other.
#. When the user scrolls the editor, the editor informs the webview where it should scroll to (and vice versa).
