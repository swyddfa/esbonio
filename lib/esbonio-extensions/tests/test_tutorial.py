import json
import pathlib

import esbonio.tutorial as tutorial
import pytest


@pytest.mark.parametrize(
    "name",
    [
        "bare_link",
        "bold",
        "bullet_list",
        "comment",
        "doctest_no_output",
        "heading",
        "image",
        "inline_code",
        "inline_link",
        "italic",
        "paragraphs",
        "note",
    ],
)
def test_notebook_translator(testdata, parse_rst, name):
    """Ensure that the notebook translator can correctly convert an rst doctree into
    the correct sequence of notebook cells."""

    rst = testdata(pathlib.Path("tutorial", name + ".rst")).decode("utf8")
    ipynb = testdata(pathlib.Path("tutorial", name + ".ipynb")).decode("utf8")

    expected = json.loads(ipynb)

    doctree = parse_rst(rst)
    translator = tutorial.NotebookTranslator(doctree)
    doctree.walkabout(translator)
    notebook = translator.asnotebook()

    # # Don't worry about cell ids
    # for cell in notebook.cells:
    #     cell.id = ""

    assert expected == notebook
