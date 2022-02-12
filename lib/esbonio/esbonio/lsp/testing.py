"""Utility functions to help with testing Language Server features."""
import asyncio
import logging
import os
import pathlib
import threading
from concurrent.futures import Future
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pygls.uris as Uri
from pygls.exceptions import JsonRpcMethodNotFound
from pygls.lsp.methods import CANCEL_REQUEST
from pygls.lsp.methods import COMPLETION
from pygls.lsp.methods import COMPLETION_ITEM_RESOLVE
from pygls.lsp.methods import DEFINITION
from pygls.lsp.methods import DOCUMENT_SYMBOL
from pygls.lsp.methods import EXIT
from pygls.lsp.methods import INITIALIZE
from pygls.lsp.methods import INITIALIZED
from pygls.lsp.methods import SHUTDOWN
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CHANGE
from pygls.lsp.methods import TEXT_DOCUMENT_DID_CLOSE
from pygls.lsp.methods import TEXT_DOCUMENT_DID_OPEN
from pygls.lsp.methods import TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS
from pygls.lsp.methods import WINDOW_LOG_MESSAGE
from pygls.lsp.methods import WINDOW_SHOW_MESSAGE
from pygls.lsp.types import ClientCapabilities
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import CompletionParams
from pygls.lsp.types import DefinitionParams
from pygls.lsp.types import Diagnostic
from pygls.lsp.types import DidChangeTextDocumentParams
from pygls.lsp.types import DidCloseTextDocumentParams
from pygls.lsp.types import DidOpenTextDocumentParams
from pygls.lsp.types import DocumentSymbol
from pygls.lsp.types import DocumentSymbolParams
from pygls.lsp.types import InitializeParams
from pygls.lsp.types import Location
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import TextDocumentContentChangeEvent
from pygls.lsp.types import TextDocumentIdentifier
from pygls.lsp.types import TextDocumentItem
from pygls.lsp.types import VersionedTextDocumentIdentifier
from pygls.protocol import LanguageServerProtocol
from pygls.server import LanguageServer
from sphinx import __version__ as __sphinx_version__

logger = logging.getLogger(__name__)


class ClientServer:
    """A class that returns a client server pair for use in tests.

    Originally based on:
    https://github.com/openlawlibrary/pygls/blob/704ff607a2a993a633fc2ad05eb95120dd34cad5/tests/conftest.py#L53
    """

    def __init__(self, server: LanguageServer):

        client_server_read, client_server_write = os.pipe()
        server_client_read, server_client_write = os.pipe()

        self.server = server
        self.server_thread = threading.Thread(
            name="Server Thread",
            target=self.server.start_io,
            args=(
                os.fdopen(client_server_read, "rb"),
                os.fdopen(server_client_write, "wb"),
            ),
        )
        self.server_thread.daemon = True

        self.client = new_test_client()
        self.client_thread = threading.Thread(
            name="Client Thread",
            target=self.client.start_io,
            args=(
                os.fdopen(server_client_read, "rb"),
                os.fdopen(client_server_write, "wb"),
            ),
        )
        self.client_thread.daemon = True

    async def start(
        self,
        root_uri: str,
        initialization_options: Optional[Dict[str, Any]] = None,
        wait=True,
    ):
        """Start the client and server components ready for testing.

        As well as starting the event loops for them both it also
        initializes the server based on the ``root_uri`` and
        ``initialization_options`` parameters. Once the response for
        the ``initialize`` request is received, it will proceed to send the
        ``initialized`` notification to trigger the initial build of the
        documentation.

        By default this method will ``await`` until the client receives the
        ``esbonio/buildComplete`` notification, though this can be disabled
        by passing ``wait=False`` (useful for preventing deadlocks in situations
        where the server is not expected to start successfully).

        Parameters
        ----------
        root_uri:
           The root uri of the project to initialize the server within
        initialization_options:
           The initializaion options to pass to the server
        wait:
           If ``True``, await until the client receives the ``esbonio/buildComplete``
           notification.
        """
        self.server_thread.start()
        self.client_thread.start()

        # Give the client and server some time to initialize
        while self.server.lsp.transport is None or self.client.lsp.transport is None:
            await asyncio.sleep(0.1)

        response = await self.client.lsp.send_request_async(
            INITIALIZE,
            InitializeParams(
                process_id=12345,
                root_uri=root_uri,
                capabilities=ClientCapabilities(),
                initialization_options=initialization_options or {},
            ),
        )

        assert "capabilities" in response

        self.client.lsp.notify(INITIALIZED)

        if wait:
            await self.client.lsp.wait_for_notification_async("esbonio/buildComplete")

        return

    async def stop(self):
        response = await self.client.lsp.send_request_async(SHUTDOWN)
        assert response is None

        self.client.lsp.notify(EXIT)
        self.server_thread.join()

        self.client._stop_event.set()
        try:
            self.client.loop._signal_handlers.clear()
        except AttributeError:
            pass

        self.client_thread.join()


def sphinx_version(eq: Optional[int] = None) -> bool:
    """Helper function for determining which version of Sphinx we are
    testing with.

    Currently this only cares about the major version number.

    Parameters
    ----------
    eq:
       When set returns ``True`` if the Sphinx version exactly matches
       what's given.
    """

    major, _, _ = [int(v) for v in __sphinx_version__.split(".")]

    if eq and major == eq:
        return True

    return False


def directive_argument_patterns(name: str, partial: str = "") -> List[str]:
    """Return a number of example directive argument patterns.

    These correspond to test cases where directive argument suggestions should be
    generated.

    Parameters
    ----------
    name:
       The name of the directive to generate suggestions for.
    partial:
       The partial argument that the user has already entered.
    """
    return [s.format(name, partial) for s in [".. {}:: {}", "   .. {}:: {}"]]


def role_patterns(partial: str = "") -> List[str]:
    """Return a number of example role patterns.

    These correspond to when role suggestions should be generated.

    Parameters
    ----------
    partial:
       The partial role name that the user has already entered
    """
    return [
        s.format(partial)
        for s in [
            "{}",
            "({}",
            "- {}",
            "   {}",
            "   ({}",
            "   - {}",
            "some text {}",
            "some text ({}",
            "   some text {}",
            "   some text ({}",
        ]
    ]


def role_target_patterns(
    name: str, partial: str = "", include_modifiers: bool = True
) -> List[str]:
    """Return a number of example role target patterns.

    These correspond to test cases where role target suggestions should be generated.

    Parameters
    ----------
    name:
       The name of the role to generate suggestions for.
    partial:
       The partial target that the user as already entered.
    include_modifiers:
       A flag to indicate if additional modifiers like ``!`` and ``~`` should be
       included in the generated patterns.
    """

    patterns = [
        ":{}:`{}",
        "(:{}:`{}",
        "- :{}:`{}",
        ":{}:`More Info <{}",
        "(:{}:`More Info <{}",
        "   :{}:`{}",
        "   (:{}:`{}",
        "   - :{}:`{}",
        "   :{}:`Some Label <{}",
        "   (:{}:`Some Label <{}",
    ]

    test_cases = [p.format(name, partial) for p in patterns]

    if include_modifiers:
        test_cases += [p.format(name, "!" + partial) for p in patterns]
        test_cases += [p.format(name, "~" + partial) for p in patterns]

    return test_cases


def intersphinx_target_patterns(name: str, project: str) -> List[str]:
    """Return a number of example intersphinx target patterns.

    These correspond to cases where target completions may be generated

    Parameters
    ----------
    name: str
       The name of the role to generate examples for
    project: str
       The name of the project to generate examples for
    """
    return [
        s.format(name, project)
        for s in [
            ":{}:`{}:",
            "(:{}:`{}:",
            ":{}:`More Info <{}:",
            "(:{}:`More Info <{}:",
            "   :{}:`{}:",
            "   (:{}:`{}:",
            "   :{}:`Some Label <{}:",
            "   (:{}:`Some Label <{}:",
        ]
    ]


async def completion_request(
    test: ClientServer, test_uri: str, text: str, character: Optional[int] = None
) -> CompletionList:
    """Make a completion request to a language server.

    Intended for use within test cases, this function simulates the opening of a
    document, inserting some text, triggering a completion request and closing it
    again.

    The file referenced by ``test_uri`` does not have to exist.

    The text to be inserted is specified through the ``text`` parameter. By default
    it's assumed that the ``text`` parameter consists of a single line of text, in fact
    this function will error if that is not the case.

    If your request requires additional context (such as directive option completions)
    it can be included but it must be delimited with a ``\\f`` character. For example,
    to represent the following scenario::

       .. image:: filename.png
          :align: center
          :
           ^

    where ``^`` represents the position from which we trigger the completion request.
    We would set ``text`` to the following
    ``.. image:: filename.png\\n   :align: center\\n\\f   :``

    Parameters
    ----------
    test:
       The client-server pair to be used to make the request.
    test_uri:
       The uri the completion request should be made within.
    text
       The text that provides the context for the completion request.
    character:
       The character index at which to make the completion request from.
       If ``None``, it will default to the end of the inserted text.
    """

    if "\f" in text:
        contents, text = text.split("\f")
    else:
        contents = ""

    logger.debug("Context text:    '%s'", contents)
    logger.debug("Insertion text: '%s'", text)
    assert "\n" not in text, "Insertion text cannot contain newlines"

    ext = pathlib.Path(Uri.to_fs_path(test_uri)).suffix
    lang_id = "python" if ext == ".py" else "rst"

    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_OPEN,
        DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=test_uri, language_id=lang_id, version=1, text=contents
            )
        ),
    )

    lines = contents.split("\n")
    line = len(lines) - 1
    insertion_point = len(lines[-1])

    logger.debug("Insertion pos: (%d, %d)", line, insertion_point)

    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_CHANGE,
        DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=test_uri, version=2),
            content_changes=[
                TextDocumentContentChangeEvent(
                    range=Range(
                        start=Position(line=line, character=insertion_point),
                        end=Position(line=line, character=insertion_point + len(text)),
                    ),
                    text=text,
                )
            ],
        ),
    )

    character = character or insertion_point + len(text)
    response = await test.client.lsp.send_request_async(
        COMPLETION,
        CompletionParams(
            text_document=TextDocumentIdentifier(uri=test_uri),
            position=Position(line=line, character=character),
        ),
    )

    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_CLOSE,
        DidCloseTextDocumentParams(text_document=TextDocumentIdentifier(uri=test_uri)),
    )

    return CompletionList(**response)


async def completion_resolve_request(
    test: ClientServer, item: CompletionItem
) -> CompletionItem:
    """Make a ``completionItem/resolve`` request to a language server.

    Intented for use within test cases, this function assumes that a
    ``textDocument/completion`` request has already been performed resulting in a list
    of ``CompletionItem`` candidates being generated. This function can then be used
    to simulate the user selecting an item and the client making a follow up
    ``completionItem/resolve`` request to the server.
    """
    response = await test.client.lsp.send_request_async(COMPLETION_ITEM_RESOLVE, item)
    return CompletionItem(**response)


async def definition_request(
    test: ClientServer, test_uri: str, position: Position
) -> List[Location]:
    """Make a definition request to a language server.

    Intended for use within test cases, this function simulates opening an
    existing file and making a definition request and closing it again.

    The file referenced by ``test_uri`` *must* exist as the actual content of the file
    will be used by the language server.

    Parameters
    ----------
    test:
       The client-server pair to be used to make the request
    test_uri:
       The uri of the file the definition request should be made within.
    position:
       The position at which to trigger the completion request.
    """

    path = pathlib.Path(Uri.to_fs_path(test_uri))
    with path.open() as f:
        contents = f.read()

    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_OPEN,
        DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=test_uri, language_id="rst", version=1, text=contents
            )
        ),
    )

    response = await test.client.lsp.send_request_async(
        DEFINITION,
        DefinitionParams(
            text_document=TextDocumentIdentifier(uri=test_uri), position=position
        ),
    )

    return [Location(**obj) for obj in response]


async def document_symbols_request(
    test: ClientServer, test_uri: str
) -> List[DocumentSymbol]:
    """Make a ``textDocument/documentSymbols`` request to a language server.

    Intended for use with test cases, this function simulates opening an existing
    file, making a document symbols request and closing it again.

    The file referenced by ``test_uri`` *must* exist as the content of the file will
    be used by the language server.

    Parameters
    ----------
    test:
       The client-server pair to be used
    test_uri:
       The uri of the file to make the ``textDocument/documentSymbols`` request within
    """

    path = pathlib.Path(Uri.to_fs_path(test_uri))
    with path.open() as f:
        contents = f.read()

    test.client.lsp.notify(
        TEXT_DOCUMENT_DID_OPEN,
        DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=test_uri, language_id="rst", version=1, text=contents
            )
        ),
    )

    response = await test.client.lsp.send_request_async(
        DOCUMENT_SYMBOL,
        DocumentSymbolParams(text_document=TextDocumentIdentifier(uri=test_uri)),
    )

    return [DocumentSymbol(**obj) for obj in response]


class ClientProtocol(LanguageServerProtocol):
    """A slightly modified version of the base protocol that allows
    us to await on notifications."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._notification_futures = {}

    def _handle_notification(self, method_name, params):

        if method_name == CANCEL_REQUEST:
            self._handle_cancel_notification(params.id)
            return

        future = self._notification_futures.pop(method_name, None)
        if future:
            future.set_result(params)

        try:
            handler = self._get_handler(method_name)
            self._execute_notification(handler, params)
        except (KeyError, JsonRpcMethodNotFound):
            logger.warning('Ignoring notification for unknown method "%s"', method_name)
        except Exception:
            logger.exception(
                'Failed to handle notification "%s": %s', method_name, params
            )

    def wait_for_notification(self, method, callback=None):

        future = Future()
        if callback:

            def wrapper(future: Future):
                result = future.result()
                callback(result)

            future.add_done_callback(wrapper)

        self._notification_futures[method] = future
        return future

    def wait_for_notification_async(self, method):
        fut = self.wait_for_notification(method)
        return asyncio.wrap_future(fut)


class Client(LanguageServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.messages: List[Any] = []
        self.diagnostics: Dict[str, List[Diagnostic]] = {}


def new_test_client() -> Client:

    client = Client(protocol_cls=ClientProtocol, loop=asyncio.new_event_loop())

    @client.feature(TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    def publish_diagnostics(client: Client, params):
        client.diagnostics[params.uri] = params.diagnostics

    @client.feature(WINDOW_LOG_MESSAGE)
    def log_message(client: Client, params):
        pass

    @client.feature(WINDOW_SHOW_MESSAGE)
    def show_message(client: Client, params):
        client.messages.append(params)

    @client.feature("esbonio/buildStart")
    def build_start(client: Client, params):
        pass

    @client.feature("esbonio/buildComplete")
    def build_complete(client: Client, params):
        pass

    return client
