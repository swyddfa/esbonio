"""Utility functions to help with testing Language Server features."""
import logging

from typing import List, Optional, Set

from pygls.types import Position
from pygls.workspace import Document

logger = logging.getLogger(__name__)


def role_target_patterns(name: str) -> List[str]:
    """Return a number of example role target patterns.

    These correspond to cases where role target completions may be generated.

    Parameters
    ----------
    name:
       The name of the role to generate examples for
    """
    return [
        s.format(name)
        for s in [":{}:`", ":{}:`More Info <", "   :{}:`", "   :{}:`Some Label <"]
    ]


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
            ":{}:`More Info <{}:",
            "   :{}:`{}:",
            "   :{}:`Some Label <{}:",
        ]
    ]


def completion_test(
    feature, text: str, expected: Optional[Set[str]], unexpected: Optional[Set[str]]
):
    """Check to see if a feature provides the correct completion suggestions.

    **Only checking CompletionItem labels is supported**

    This function takes the given ``feature`` and calls it in the same manner as the
    real language server so that it can simulate real usage without being a full blown
    integration test.

    This requires ``suggest_triggers`` to be set and it to have a working ``suggest``
    method.

    Completions will be asked for with the cursor's position to be at the end of the
    inserted ``text`` in a blank document by default. If your test case requires
    additional context this can be included in ``text`` delimited by a ``\\f`` character.

    For example to pass text representing the following scenario (``^`` represents the
    user's cursor)::

       .. image:: filename.png
          :align: center
          :
           ^

    The ``text`` parameter should be set to
    ``.. image:: filename.png\\n   :align: center\\n\\f   :``. It's important to note that
    newlines **cannot** come after the ``\\f`` character.

    If you want to test the case where no completions should be suggested, pass ``None``
    to both the ``expected`` and ``unexpected`` parameters.

    Parameters
    ----------
    feature:
       An instance of the language service feature to test.
    text:
       The text to offer completion suggestions for.
    expected:
       The set of completion item labels you expect to see in the output.
    unexpected:
       The set of completion item labels you do *not* expect to see in the output.
    """

    if "\f" in text:
        contents, text = text.split("\f")
    else:
        contents = ""

    logger.debug("Context text:    '%s'", contents)
    logger.debug("Insertsion text: '%s'", text)
    assert "\n" not in text, "Insertion text cannot contain newlines"

    document = Document("file:///test_doc.rst", contents)
    position = Position(len(document.lines), len(text) - 1)

    results = []
    for trigger in feature.suggest_triggers:
        match = trigger.match(text)
        logger.debug("Match: %s", match)

        if match:
            results += feature.suggest(match, document, position)

    items = {item.label for item in results}

    logger.debug("Results:    %s", items)
    logger.debug("Expected:   %s", expected)
    logger.debug("Unexpected: %s", unexpected)

    if expected is None:
        assert len(items) == 0
    else:
        assert expected == items & expected
        assert set() == items & unexpected
