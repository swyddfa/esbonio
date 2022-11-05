import pathlib

import nbformat.v4 as nbformat
import pytest

import esbonio.tutorial as tutorial


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
    json = testdata(pathlib.Path("tutorial", name + ".ipynb")).decode("utf8")

    nb = nbformat.reads(json)

    # Don't worry about different minor version numbers
    nb.nbformat_minor = None

    doctree = parse_rst(rst)

    translator = tutorial.NotebookTranslator(doctree)
    doctree.walkabout(translator)

    notebook = translator.asnotebook()
    notebook.nbformat_minor = None

    # Don't worry about cell ids
    for cell in notebook.cells:
        cell.id = ""

    actual = nbformat.writes(notebook)
    expected = nbformat.writes(nb)

    assert expected == actual
