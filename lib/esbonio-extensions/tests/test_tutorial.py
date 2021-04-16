import pathlib

import nbformat.v4 as nbformat
import py.test

import esbonio.tutorial as tutorial


@py.test.mark.parametrize(
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
        "literal_block",
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

    actual = nbformat.writes(notebook)
    expected = nbformat.writes(nb)

    assert expected == actual
