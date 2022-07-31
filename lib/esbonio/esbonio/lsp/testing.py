"""Utility functions to help with testing Language Server features."""
import logging
import pathlib
from typing import List
from typing import Optional
from typing import Union

import pygls.uris as Uri
from pygls.lsp.types import CompletionItem
from pygls.lsp.types import CompletionList
from pygls.lsp.types import Hover
from pygls.lsp.types import Position
from pytest_lsp import Client
from pytest_lsp import make_test_client
from sphinx import __version__ as __sphinx_version__

logger = logging.getLogger(__name__)


def _noop(*args, **kwargs):
    ...


def make_esbonio_client(*args, **kwargs) -> Client:
    """Construct a pytest-lsp client that is aware of esbonio specific messages"""
    client = make_test_client(*args, **kwargs)
    client.feature("esbonio/buildStart")(_noop)
    client.feature("esbonio/buildComplete")(_noop)

    return client


def sphinx_version(
    eq: Optional[int] = None,
    lt: Optional[int] = None,
    lte: Optional[int] = None,
    gt: Optional[int] = None,
    gte: Optional[int] = None,
) -> bool:
    """Helper function for determining which version of Sphinx we are
    testing with.

    .. note::

       Currently this function only considers the major version number.

    Parameters
    ----------
    eq
       When set, this function returns ``True`` if Sphinx's version is exactly
       what's given.

    gt
       When set, this function returns ``True`` if Sphinx's version is strictly
       greater than what's given

    gte
       When set, this function returns ``True`` if Sphinx's version is greater than
       or equal to what's given

    lt
       When set, this function returns ``True`` if Sphinx's version is strictly
       less than what's given

    lte
       When set, this function returns ``True`` if Sphinx's version is less than
       or equal to what's given

    """

    major, _, _ = [int(v) for v in __sphinx_version__.split(".")]

    if eq is not None:
        return major == eq

    if gt is not None:
        return major > gt

    if gte is not None:
        return major >= gte

    if lt is not None:
        return major < lt

    if lte is not None:
        return major <= lte

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
    client: Client, test_uri: str, text: str, character: Optional[int] = None
) -> Union[CompletionList, List[CompletionItem], None]:
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
       The client used to make the request.
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

    client.notify_did_open(test_uri, lang_id, contents)

    lines = contents.split("\n")
    line = len(lines) - 1
    insertion_point = len(lines[-1])

    client.notify_did_change(test_uri, text, line, insertion_point),

    character = character or insertion_point + len(text)
    response = await client.completion_request(test_uri, line, character)

    client.notify_did_close(test_uri)
    return response


async def hover_request(
    client: Client, test_uri: str, text: str, position: Position
) -> Optional[Hover]:
    """Make a hover request to a language server.

    Intended for use within test cases, this function simulates the opening of a
    document containing some text, triggering a hover request and closing it again.

    The file referenced by ``test_uri`` does not have to exist.

    Parameters
    ----------
    test
       The client used to make the request.

    test_uri
       The uri the completion request should be made within.

    text
       The text that provides the context for the hover request.

    position
       The position at which to make the hover request from.
    """
    ext = pathlib.Path(Uri.to_fs_path(test_uri)).suffix
    lang_id = "python" if ext == ".py" else "rst"

    client.notify_did_open(test_uri, lang_id, text)
    response = await client.hover_request(test_uri, position)

    client.notify_did_close(test_uri)
    return response
