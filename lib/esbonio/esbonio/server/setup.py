from __future__ import annotations

import importlib
import inspect
import pathlib
import typing
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Set
from typing import Type

from lsprotocol import types

from . import Uri

if typing.TYPE_CHECKING:
    from .server import EsbonioLanguageServer


def create_language_server(
    server_cls: Type[EsbonioLanguageServer], modules: Iterable[str], *args, **kwargs
) -> EsbonioLanguageServer:
    """Create a new language server instance.

    Parameters
    ----------
    server_cls:
       The class definition to create the server from.
    modules:
       The list of modules that should be loaded.
    args, kwargs:
       Any additional arguments that should be passed to the language server's
       constructor.
    """
    server = server_cls(*args, **kwargs)

    for module in modules:
        _load_module(server, module)

    _configure_lsp_methods(server)
    _configure_completion(server)

    return server


def _configure_lsp_methods(server: EsbonioLanguageServer):
    """Configure method handlers for the portions of the LSP spec we support."""

    @server.feature(types.INITIALIZE)
    async def on_initialize(ls: EsbonioLanguageServer, params: types.InitializeParams):
        ls.initialize(params)
        await call_features(ls, "initialize", params)

    @server.feature(types.INITIALIZED)
    async def on_initialized(
        ls: EsbonioLanguageServer, params: types.InitializedParams
    ):
        await ls.initialized(params)
        await call_features(ls, "initialized", params)

    @server.feature(types.SHUTDOWN)
    async def on_shutdown(ls: EsbonioLanguageServer, params: None):
        ls.lsp_shutdown(params)
        await call_features(ls, "shutdown", params)

    @server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
    async def on_document_change(
        ls: EsbonioLanguageServer, params: types.DidChangeTextDocumentParams
    ):
        await call_features(ls, "document_change", params)

    @server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
    async def on_document_close(
        ls: EsbonioLanguageServer, params: types.DidCloseTextDocumentParams
    ):
        await call_features(ls, "document_close", params)

    @server.feature(types.TEXT_DOCUMENT_DID_OPEN)
    async def on_document_open(
        ls: EsbonioLanguageServer, params: types.DidOpenTextDocumentParams
    ):
        await call_features(ls, "document_open", params)

    @server.feature(types.TEXT_DOCUMENT_DID_SAVE)
    async def on_document_save(
        ls: EsbonioLanguageServer, params: types.DidSaveTextDocumentParams
    ):
        # Record the version number of the document
        doc = ls.workspace.get_document(params.text_document.uri)
        doc.saved_version = doc.version or 0

        await call_features(ls, "document_save", params)

    @server.feature(
        types.TEXT_DOCUMENT_DIAGNOSTIC,
        types.DiagnosticOptions(
            identifier="esbonio",
            inter_file_dependencies=True,
            workspace_diagnostics=True,
        ),
    )
    async def on_document_diagnostic(
        ls: EsbonioLanguageServer, params: types.DocumentDiagnosticParams
    ):
        """Handle a ``textDocument/diagnostic`` request."""
        doc_uri = Uri.parse(params.text_document.uri).resolve()
        items = []

        for (_, uri), diags in ls._diagnostics.items():
            if uri.resolve() == doc_uri:
                items.extend(diags)

        # TODO: Detect no changes and send 'unchanged' responses
        return types.RelatedFullDocumentDiagnosticReport(
            items=items,
            kind=types.DocumentDiagnosticReportKind.Full,
        )

    @server.feature(types.WORKSPACE_DIAGNOSTIC)
    async def on_workspace_diagnostic(
        ls: EsbonioLanguageServer, params: types.WorkspaceDiagnosticParams
    ):
        """Handle a ``workspace/diagnostic`` request."""
        diagnostics: Dict[Uri, List[types.Diagnostic]] = {}

        for (_, uri), diags in ls._diagnostics.items():
            diagnostics.setdefault(uri, []).extend(diags)

        # TODO: Detect no changes and send 'unchanged' responses
        reports = []
        for uri, items in diagnostics.items():
            reports.append(
                types.WorkspaceFullDocumentDiagnosticReport(
                    uri=str(uri),
                    items=items,
                    kind=types.DocumentDiagnosticReportKind.Full,
                )
            )

        # Typing issues should be fixed in a future version of lsprotocol
        # see: https://github.com/microsoft/lsprotocol/pull/285
        return types.WorkspaceDiagnosticReport(items=reports)  # type: ignore[arg-type]

    @server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    async def on_document_symbol(
        ls: EsbonioLanguageServer, params: types.DocumentSymbolParams
    ):
        result = await return_first_result(ls, "document_symbol", params)
        return result

    @server.feature(types.WORKSPACE_SYMBOL)
    async def on_workspace_symbol(
        ls: EsbonioLanguageServer, params: types.WorkspaceSymbolParams
    ):
        result = await return_first_result(ls, "workspace_symbol", params)
        if len(result) == 0:
            return None

        return result

    @server.feature(types.WORKSPACE_DID_CHANGE_CONFIGURATION)
    async def on_did_change_configuration(
        ls: EsbonioLanguageServer, params: types.DidChangeConfigurationParams
    ):
        ls.logger.debug("%s: %s", types.WORKSPACE_DID_CHANGE_CONFIGURATION, params)
        await ls.configuration.update_workspace_configuration()

    @server.feature(types.WORKSPACE_DID_CHANGE_WATCHED_FILES)
    async def on_did_change_watched_files(
        ls: EsbonioLanguageServer, params: types.DidChangeWatchedFilesParams
    ):
        ls.logger.debug("%s: %s", types.WORKSPACE_DID_CHANGE_WATCHED_FILES, params)
        # TODO: Handle deleted files.
        paths = [pathlib.Path(Uri.parse(event.uri)) for event in params.changes]
        await ls.configuration.update_file_configuration(paths)


def _configure_completion(server: EsbonioLanguageServer):
    """Configuration completion handlers."""

    trigger_characters: Set[str] = set()

    for _, feature in server:
        if feature.completion_trigger is None:
            continue

        trigger_characters.update(feature.completion_trigger.characters)

    @server.feature(
        types.TEXT_DOCUMENT_COMPLETION,
        types.CompletionOptions(
            trigger_characters=list(trigger_characters),
            resolve_provider=True,
        ),
    )
    async def on_completion(ls: EsbonioLanguageServer, params: types.CompletionParams):
        uri = params.text_document.uri
        pos = params.position
        doc = ls.workspace.get_text_document(uri)
        language = ls.get_language_at(doc, pos)

        items = []

        for cls, feature in ls:
            if not feature.completion_trigger:
                continue

            context = feature.completion_trigger(
                uri=Uri.parse(uri),
                params=params,
                document=doc,
                language=language,
                client_capabilities=ls.client_capabilities,
            )

            if context is None:
                continue

            ls.logger.debug("%s", context)
            name = f"{cls.__name__}"

            try:
                result = feature.completion(context)
                if inspect.isawaitable(result):
                    result = await result
            except Exception:
                ls.logger.exception("Error in '%s.complete' handler", name)
                continue

            for item in result or []:
                item.data = {"source_feature": name, **(item.data or {})}  # type: ignore
                items.append(item)

        if len(items) > 0:
            return types.CompletionList(is_incomplete=False, items=items)

    @server.feature(types.COMPLETION_ITEM_RESOLVE)
    def on_completion_resolve(
        ls: EsbonioLanguageServer, item: types.CompletionItem
    ) -> types.CompletionItem:
        # source = (item.data or {}).get("source_feature", "")  # type: ignore
        # feature = ls.get_feature(source)

        # if not feature:
        #     ls.logger.error(
        #         "Unable to resolve completion item, unknown source: '%s'", source
        #     )
        #     return item

        # return feature.completion_resolve(item)
        return item


async def call_features(ls: EsbonioLanguageServer, method: str, *args, **kwargs):
    """Call all features."""

    for cls, feature in ls:
        try:
            impl = getattr(feature, method)

            result = impl(*args, **kwargs)
            if inspect.isawaitable(result):
                await result

        except Exception:
            name = f"{cls.__name__}"
            ls.logger.error("Error in '%s.%s' handler", name, method, exc_info=True)


async def gather_results(ls: EsbonioLanguageServer, method: str, *args, **kwargs):
    """Call all features, gathering all results into a list."""
    results: List[Any] = []
    for cls, feature in ls:
        try:
            impl = getattr(feature, method)

            result = impl(*args, **kwargs)
            if inspect.isawaitable(result):
                items = await result
            else:
                items = result

            if isinstance(items, list):
                results.extend(items)
            elif items is not None:
                results.append(items)

        except Exception:
            name = f"{cls.__name__}"
            ls.logger.error("Error in '%s.%s' handler", name, method, exc_info=True)

    return results


async def return_first_result(ls: EsbonioLanguageServer, method: str, *args, **kwargs):
    """Call all features, returning the first non ``None`` result we find."""

    for cls, feature in ls:
        try:
            impl = getattr(feature, method)

            result = impl(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result

            if result is not None:
                return result

        except Exception:
            name = f"{cls.__name__}"
            ls.logger.error("Error in '%s.%s' handler", name, method, exc_info=True)


def _load_module(server: EsbonioLanguageServer, modname: str):
    """Load an extension module by calling its ``esbonio_setup`` function, if it exists."""

    try:
        module = importlib.import_module(modname)
    except ImportError:
        server.logger.error("Unable to import module '%s'", modname, exc_info=True)
        return None

    setup = getattr(module, "esbonio_setup", None)
    if setup is None:
        server.logger.debug(
            "Skipping module '%s', missing 'esbonio_setup' function", modname
        )
        return None

    server.load_extension(modname, setup)
