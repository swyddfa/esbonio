
Commands
""""""""

The VSCode extension provides a number of commands accessible through VSCode's command
palette (:kbd:`Ctrl+Shift+P`) and in some cases via a default keybinding.

Insert Inline Link - ``esbonio.insert.inlineLink`` - :kbd:`Alt+l`
   This inserts an inline link into the current document, for example::

      `Sphinx <https://www.sphinx-doc.org/en/master>`_ is a fantastic
      documentation tool

   Upon triggering the command vscode will first prompt you for the URL you wish to
   link to followed by the label you want the reader to see. It will then insert the link
   into the document at the position of your cursor.

   .. tip::

      If you select some text before triggering the command, the text you selected will be
      used as the link's label.

Insert Link - ``esbonio.insert.link`` - :kbd:`Alt+Shift+l`
   This inserts a "named link" into the current document, for example::

      `Sphinx`_ is a fantastic documentation tool

      .. _Sphinx: https://www.sphinx-doc.org/en/master

   Upon triggering the command vscode will first prompt you for the URL you wish to
   link to followed by the label you want the reader to see. It will then insert both
   the definition at the end of the document and the reference at the position of your
   cursor.

   .. tip::

      If you select some text before triggering the command, the text you selected will be
      used as the link's label.

Open Preview - ``esbonio.preview.open``
   This will open a webview in the current editor window showing the latest html build of the
   document being edited.

Open Preview to the Side - ``esbonio.preview.openSide``
   Much like the *Open Preview* command, this will open a webview showing the latest build
   for the current document but to the side of the editor window. Additionally, as you change
   between source files the preview will automatically update to show the page you are
   currently working on.

Install Language Server - ``esbonio.server.install``
   This can be used to manually install the language server into the current environment

Restart Language Server - ``esbonio.server.restart``
   The can be used to kill and restart the language server

Update Language Server - ``esbonio.server.update``
   This can be used to manually trigger an update to the language server
