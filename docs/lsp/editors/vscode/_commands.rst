
The Esbonio VSCode extension also provides a number of commands accessible through VSCode's command
palette (:kbd:`Ctrl+Shift+P`).

``esbonio.preview.open``
   This will open a webview in the current editor window showing the latest html build of the
   document being edited.

``esbonio.preview.openSide``
   Much like the ``esbonio.preview.open`` command, this will open a webview showing the latest build
   for the current document but to the side of the editor window. Additionally, as you change
   between source files the preview will automatically update to show the page you are
   currently working on.

``esbonio.server.restart``
   This will kill and restart the language server

``esbonio.server.install``
   This can be used to manually install the language server into the current environment

``esbonio.server.update``
   This can be used to manually trigger an update to the language server
