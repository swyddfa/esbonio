import pathlib
from typing import Generator

from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionItemKind
from pygls.lsp.types import Position
from pygls.lsp.types import Range
from pygls.lsp.types import TextEdit

from esbonio.lsp.rst import CompletionContext


def path_to_completion_item(
    context: CompletionContext, path: pathlib.Path
) -> CompletionItem:
    """Create the ``CompletionItem`` for the given path.

    In the case where there are multiple filepath components, this function needs to
    provide an appropriate ``TextEdit`` so that the most recent entry in the path can
    be easily edited - without clobbering the existing path.

    Also bear in mind that this function must play nice with both role target and
    directive argument completions.
    """

    new_text = f"{path.name}"
    kind = CompletionItemKind.Folder if path.is_dir() else CompletionItemKind.File

    # If we can't find the '/' we may as well not bother with a `TextEdit` and let the
    # `Roles` feature provide the default handling.
    start = _find_start_char(context)
    if start == -1:
        insert_text = new_text
        filter_text = None
        text_edit = None
    else:

        start += 1
        _, end = context.match.span()
        prefix = context.match.group(0)[start:]

        insert_text = None
        filter_text = (
            f"{prefix}{new_text}"  # Needed so VSCode will actually show the results.
        )

        text_edit = TextEdit(
            range=Range(
                start=Position(line=context.position.line, character=start),
                end=Position(line=context.position.line, character=end),
            ),
            new_text=new_text,
        )

    return CompletionItem(
        label=new_text,
        kind=kind,
        insert_text=insert_text,
        filter_text=filter_text,
        text_edit=text_edit,
    )


def _find_start_char(context: CompletionContext) -> int:
    matched_text = context.match.group(0)
    idx = matched_text.find("/")

    while True:
        next_idx = matched_text.find("/", idx + 1)
        if next_idx == -1:
            break

        idx = next_idx

    return idx


def complete_filepaths(base: str, partial: str) -> Generator[pathlib.Path, None, None]:
    """Generate filepath completion suggestions relative to the given base.

    This function is for "docutils style" behaviour where the path is relative to the
    current document.

    Parameters
    ----------
    base
       The directory containing the current document

    partial
       The existing path entered so far.
    """

    candidate_dir = pathlib.Path(base) / pathlib.Path(partial)
    if partial and not partial.endswith("/"):
        candidate_dir = candidate_dir.parent

    return candidate_dir.glob("*")


def complete_sphinx_filepaths(
    srcdir: str, base: str, partial: str
) -> Generator[pathlib.Path, None, None]:
    """Generate filepath completion suggestions relative to the given base or ``srcdir``.

    This function is for "sphinx style" behaviour where the path is relative to the
    current document *unless* ``partial`` starts with a ``/`` character. In this case
    completions should be relative to the given ``srcdir``.

    Parameters
    ----------
    srcdir
       The ``srcdir`` of the project, used when ``partial`` starts with a ``/``.

    base
       The directory containing the current document.

    partial
       The existing path entered so far.
    """

    if partial and partial.startswith("/"):
        candidate_dir = pathlib.Path(srcdir)

        # Be sure to take off the leading '/' character, otherwise the partial
        # path will wipe out the srcdir when concatenated...
        partial = partial[1:]
    else:
        candidate_dir = pathlib.Path(base)

    candidate_dir /= pathlib.Path(partial)
    if partial and not partial.endswith("/"):
        candidate_dir = candidate_dir.parent

    return candidate_dir.glob("*")
