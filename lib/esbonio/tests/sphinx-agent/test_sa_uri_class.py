# Test cases originally based on:
# https://github.com/microsoft/vscode/blob/5653420433692dc4269ad39adbc143e3438af179/src/vs/base/test/common/uri.test.ts
import os.path
import pathlib
from typing import Any
from typing import Dict

import pytest

from esbonio.sphinx_agent.types import IS_WIN
from esbonio.sphinx_agent.types import Uri


def test_uri_is_pathlike():
    """Ensure that a Uri implements the ``os.PathLike`` protocol and that it works as
    expected."""

    uri = Uri.for_file(__file__)
    assert os.fspath(uri) == os.fspath(__file__)
    assert os.path.normpath(os.path.join(uri, "..")) == os.path.normpath(
        os.path.join(__file__, "..")
    )
    assert pathlib.Path(uri) == pathlib.Path(__file__)


def test_uri_hashable():
    """Ensure that the Uri class is hashable, so that it can be used as dictionary
    keys etc."""

    uri = Uri.for_file("file.txt")
    assert hash(uri) != 0


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (Uri.parse("file:///a.txt"), 1, False),
        (Uri.create(scheme="file"), Uri.create(scheme="file"), True),
        (Uri.create(scheme="file"), Uri.create(scheme="http"), False),
        (
            Uri.create(scheme="file", query="a"),
            Uri.create(scheme="file", query="a"),
            True,
        ),
        (
            Uri.create(scheme="file", query="a"),
            Uri.create(scheme="file", query="b"),
            False,
        ),
        (
            Uri.create(scheme="file", authority="a"),
            Uri.create(scheme="file", authority="a"),
            True,
        ),
        (
            Uri.create(scheme="file", authority="a"),
            Uri.create(scheme="file", authority="b"),
            False,
        ),
        (
            Uri.create(scheme="file", fragment="a"),
            Uri.create(scheme="file", fragment="a"),
            True,
        ),
        (
            Uri.create(scheme="file", fragment="a"),
            Uri.create(scheme="file", fragment="b"),
            False,
        ),
        (
            Uri.create(scheme="http", path="a/b"),
            Uri.create(scheme="http", path="a/b"),
            True,
        ),
        (
            Uri.create(scheme="http", path="a/b"),
            Uri.create(scheme="http", path="a/B"),
            False,
        ),
        pytest.param(
            Uri.create(scheme="file", path="a/b"),
            Uri.create(scheme="file", path="a/B"),
            False,
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            # Filepaths on Windows are case insensitive
            Uri.create(scheme="file", path="a/b"),
            Uri.create(scheme="file", path="a/B"),
            True,
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
    ],
)
def test_uri_eq(a: Uri, b: Any, expected: bool):
    """Ensure that we have implemented ``__eq__`` for Uris correctly."""
    assert (a == b) is expected


@pytest.mark.parametrize(
    "path, expected",
    [
        ("c:/win/path", "file:///c%3A/win/path"),
        ("C:/win/path", "file:///c%3A/win/path"),
        ("c:/win/path/", "file:///c%3A/win/path/"),
        ("/c:/win/path", "file:///c%3A/win/path"),
        pytest.param(
            r"c:\win\path",
            "file:///c%3A/win/path",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            r"c:\win/path",
            "file:///c%3A/win/path",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            r"c:\win\path",
            "file:///c%3A%5Cwin%5Cpath",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            r"c:\win/path",
            "file:///c%3A%5Cwin/path",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A Windows"),
        ),
    ],
)
def test_file_uri_to_string(path: str, expected: str):
    """Ensure that we can convert ``file://`` based uris to strings correctly."""
    assert str(Uri.for_file(path)) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        pytest.param(
            "c:/win/path",
            "c:/win/path",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "c:/win/path/",
            "c:/win/path/",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "C:/win/path",
            "c:/win/path",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "/c:/win/path",
            "c:/win/path",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "./c/win/path",
            "/./c/win/path",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        # -------------------
        pytest.param(
            r"c:\win\path",
            r"c:\win\path",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            r"c:\win/path",
            r"c:\win\path",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "c:/win/path",
            r"c:\win\path",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "c:/win/path/",
            "c:\\win\\path\\",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "C:/win/path",
            r"c:\win\path",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "/c:/win/path",
            r"c:\win\path",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "./c/win/path",
            r"\.\c\win\path",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
    ],
)
def test_file_uri_fs_path(path: str, expected: str):
    """Ensure that we can compute an fs path from a uri correctly."""
    assert Uri.for_file(path).fs_path == expected


@pytest.mark.parametrize(
    "src, expected",
    [
        pytest.param(
            "file:///c:/alex.txt",
            "c:/alex.txt",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "file://monacotools/folder/isi.txt",
            "//monacotools/folder/isi.txt",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "file://monacotools1/certificates/SSL/",
            "//monacotools1/certificates/SSL/",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "file:///c:/Source/Z%C3%BCrich%20or%20Zurich%20(%CB%88zj%CA%8A%C9%99r%C9%AAk,"
            "/Code/resources/app/plugins",
            "c:/Source/Zürich or Zurich (ˈzjʊərɪk,/Code/resources/app/plugins",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        # -------------------
        pytest.param(
            "file:///c:/alex.txt",
            r"c:\alex.txt",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "file://monacotools/folder/isi.txt",
            r"\\monacotools\folder\isi.txt",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "file://monacotools1/certificates/SSL/",
            "\\\\monacotools1\\certificates\\SSL\\",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "file:///c:/Source/Z%C3%BCrich%20or%20Zurich%20(%CB%88zj%CA%8A%C9%99r%C9%AAk,"
            "/Code/resources/app/plugins",
            r"c:\Source\Zürich or Zurich (ˈzjʊərɪk,\Code\resources\app\plugins",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
    ],
)
def test_uri_from_fs_path(src: str, expected: str):
    """Ensure that we can compute an ``fs_path`` correctly, create a uri from it and
    have it be equivalent to the original uri."""

    uri = Uri.parse(src)
    assert uri.fs_path == expected

    uri2 = Uri.for_file(uri.fs_path)
    assert uri2.fs_path == expected
    assert str(uri) == str(uri2)


def test_fs_path_with_no_path():
    """Ensure that the ``fs_path`` property behaves as expected when the uri contains
    no path."""
    uri = Uri.parse("file://%2Fhome%2Fticino%2Fdesktop%2Fcpluscplus%2Ftest.cpp")
    assert uri.authority == "/home/ticino/desktop/cpluscplus/test.cpp"
    assert uri.path == "/"

    expected = "\\" if IS_WIN else "/"
    assert uri.fs_path == expected


@pytest.mark.parametrize(
    "uri, expected",
    [
        (
            Uri.create(scheme="http", authority="www.example.com", path="/my/path"),
            "http://www.example.com/my/path",
        ),
        (
            Uri.create(scheme="http", authority="www.EXAMPLE.com", path="/my/path"),
            "http://www.example.com/my/path",
        ),
        (Uri.create(scheme="http", path="my/path"), "http:/my/path"),
        (Uri.create(scheme="http", path="/my/path"), "http:/my/path"),
        (
            Uri.create(scheme="http", authority="example.com", query="test=true"),
            "http://example.com/?test%3Dtrue",
        ),
        (
            Uri.create(scheme="http", authority="example.com", fragment="test=true"),
            "http://example.com/#test%3Dtrue",
        ),
        (Uri.parse("stuff:?qüery"), "stuff:?q%C3%BCery"),
        (Uri.parse("file://sh%c3%a4res/path"), "file://sh%C3%A4res/path"),
        (
            Uri.parse("untitled:c:/Users/jreiken/Code/abc.txt"),
            "untitled:c%3A/Users/jreiken/Code/abc.txt",
        ),
        (
            Uri.parse("untitled:C:/Users/jreiken/Code/abc.txt"),
            "untitled:c%3A/Users/jreiken/Code/abc.txt",
        ),
        (
            Uri.for_file(
                "/Users/jrieken/Code/_samples/18500/Mödel + Other Thîngß/model.js"
            ),
            "file:///Users/jrieken/Code/_samples/18500/M%C3%B6del%20%2B%20Other%20Th%C3%AEng%C3%9F/model.js",
        ),
        (Uri.parse("http://localhost:8080/far"), "http://localhost:8080/far"),
        (Uri.parse("http://löcalhost:8080/far"), "http://l%C3%B6calhost:8080/far"),
        (Uri.parse("http://foo:bar@localhost/far"), "http://foo:bar@localhost/far"),
        (Uri.parse("http://foo@localhost/far"), "http://foo@localhost/far"),
        (
            Uri.parse("http://foo:bAr@localhost:8080/far"),
            "http://foo:bAr@localhost:8080/far",
        ),
        (Uri.parse("http://foo@localhost:8080/far"), "http://foo@localhost:8080/far"),
        (
            Uri.parse("http://föö:bör@löcalhost:8080/far"),
            "http://f%C3%B6%C3%B6:b%C3%B6r@l%C3%B6calhost:8080/far",
        ),
        (
            Uri.parse("https://go.microsoft.com/fwlink/?LinkId=518008"),
            "https://go.microsoft.com/fwlink/?LinkId%3D518008",
        ),
        (
            Uri.parse("https://go.microsoft.com/fwlink/?LinkId=518008&foö&ké¥=üü"),
            "https://go.microsoft.com/fwlink/?LinkId%3D518008%26fo%C3%B6%26k%C3%A9%C2%A5%3D%C3%BC%C3%BC",
        ),
    ],
)
def test_uri_to_string_with_encoding(uri: Uri, expected: str):
    """Ensure that we can convert a uri to a string correctly with encoding"""
    assert str(uri) == expected


@pytest.mark.parametrize(
    "uri, expected",
    [
        (
            Uri.create(scheme="http", authority="example.com", query="test=true"),
            "http://example.com/?test=true",
        ),
        (
            Uri.create(scheme="http", authority="example.com", fragment="test=true"),
            "http://example.com/#test=true",
        ),
        (
            Uri.create(scheme="http", path="/api/files/test.me", query="t=1234"),
            "http:/api/files/test.me?t=1234",
        ),
        (
            Uri.parse("https://go.microsoft.com/fwlink/?LinkId=518008"),
            "https://go.microsoft.com/fwlink/?LinkId=518008",
        ),
        (
            Uri.parse("https://go.microsoft.com/fwlink/?LinkId=518008&foö&ké¥=üü"),
            "https://go.microsoft.com/fwlink/?LinkId=518008&foö&ké¥=üü",
        ),
        (
            Uri.parse("https://twitter.com/search?src=typd&q=%23tag"),
            "https://twitter.com/search?src=typd&q=%23tag",
        ),
    ],
)
def test_uri_to_string_without_encoding(uri: Uri, expected: str):
    """Ensure that we can convert a uri to a string correctly with encoding"""
    assert uri.as_string(encode=False) == expected


def test_uri_parse_encode():
    uri = Uri.parse("file://shares/pröjects/c%23/#l12")
    assert uri.authority == "shares"
    assert uri.path == "/pröjects/c#/"
    assert uri.fragment == "l12"
    assert str(uri) == "file://shares/pr%C3%B6jects/c%23/#l12"
    assert uri.as_string(encode=False) == "file://shares/pröjects/c%23/#l12"

    uri2 = Uri.parse(str(uri))
    uri3 = Uri.parse(uri.as_string(encode=False))
    assert uri2.authority == uri3.authority
    assert uri2.path == uri3.path
    assert uri2.query == uri3.query
    assert uri2.fragment == uri3.fragment


@pytest.mark.parametrize(
    "before, args, expected",
    [
        (
            Uri.parse("before:some/file/path"),
            dict(scheme="after"),
            "after:some/file/path",
        ),
        (
            Uri.create(scheme="s"),
            dict(scheme="http", path="/api/files/test.me", query="t=1234"),
            "http:/api/files/test.me?t%3D1234",
        ),
        (
            Uri.create(scheme="s"),
            dict(
                scheme="http", authority="", path="/api/files/test.me", query="t=1234"
            ),
            "http:/api/files/test.me?t%3D1234",
        ),
        (
            Uri.create(scheme="s"),
            dict(
                scheme="https", authority="", path="/api/files/test.me", query="t=1234"
            ),
            "https:/api/files/test.me?t%3D1234",
        ),
        (
            Uri.create(scheme="s"),
            dict(
                scheme="HTTP", authority="", path="/api/files/test.me", query="t=1234"
            ),
            "HTTP:/api/files/test.me?t%3D1234",
        ),
        (
            Uri.create(scheme="s"),
            dict(
                scheme="HTTPS", authority="", path="/api/files/test.me", query="t=1234"
            ),
            "HTTPS:/api/files/test.me?t%3D1234",
        ),
        (
            Uri.create(scheme="s"),
            dict(scheme="boo", authority="", path="/api/files/test.me", query="t=1234"),
            "boo:/api/files/test.me?t%3D1234",
        ),
        (Uri.parse("scheme://authority/path"), dict(authority=""), "scheme:/path"),
        (Uri.parse("scheme://authority/path"), dict(authority=None), "scheme:/path"),
        (Uri.parse("scheme://authority/path"), dict(path=""), "scheme://authority"),
        (Uri.parse("scheme://authority/path"), dict(path=None), "scheme://authority"),
    ],
)
def test_uri_where(before: Uri, args: Dict[str, str], expected: str):
    """Ensure that we can transform uris correctly."""
    assert str(before.where(**args)) == expected


@pytest.mark.parametrize(
    "before, args, message",
    [
        (Uri.parse("foo:bar/path"), dict(scheme=None), "URIs must have a scheme"),
        (Uri.parse("foo:bar/path"), dict(scheme="fai:l"), "Invalid scheme"),
        (Uri.parse("foo:bar/path"), dict(scheme="fäil"), "Invalid scheme"),
        (
            Uri.parse("foo:bar/path"),
            dict(authority="fail"),
            "Paths with an authority must start with a slash '/'",
        ),
        (
            Uri.parse("foo:bar/path"),
            dict(path="//fail"),
            "Paths without an authority cannot start with two slashes '//'",
        ),
    ],
)
def test_uri_where_validation(before: Uri, args: Dict[str, str], message: str):
    """Ensure that transformed uris are validated"""

    with pytest.raises(ValueError) as e:
        before.where(**args)

    assert message in str(e)


@pytest.mark.parametrize(
    "uri, expected",
    [
        (
            "http:/api/files/test.me?t=1234",
            Uri.create(scheme="http", path="/api/files/test.me", query="t=1234"),
        ),
        (
            "http://api/files/test.me?t=1234",
            Uri.create(
                scheme="http", authority="api", path="/files/test.me", query="t=1234"
            ),
        ),
        ("file:///c:/test/me", Uri.create(scheme="file", path="/c:/test/me")),
        (
            "file://shares/files/c%23/p.cs",
            Uri.create(scheme="file", authority="shares", path="/files/c#/p.cs"),
        ),
        (
            "file:///c:/Source/Z%C3%BCrich%20or%20Zurich%20(%CB%88zj%CA%8A%C9%99r%C9%AAk,"
            "/Code/resources/app/plugins/c%23/plugin.json",
            Uri.create(
                scheme="file",
                path="/c:/Source/Zürich or Zurich (ˈzjʊərɪk,/Code/resources/app/plugins/c#/plugin.json",
            ),
        ),
        ("file:///c:/test %25/path", Uri.create(scheme="file", path="/c:/test %/path")),
        ("inmemory:", Uri.create(scheme="inmemory")),
        ("foo:api/files/test", Uri.create(scheme="foo", path="api/files/test")),
        ("file:?q", Uri.create(scheme="file", query="q")),
        ("file:#d", Uri.create(scheme="file", fragment="d")),
        ("f3ile:#d", Uri.create(scheme="f3ile", fragment="d")),
        ("foo+bar:path", Uri.create(scheme="foo+bar", path="path")),
        ("foo-bar:path", Uri.create(scheme="foo-bar", path="path")),
        ("foo.bar:path", Uri.create(scheme="foo.bar", path="path")),
    ],
)
def test_uri_parse(uri: str, expected: Uri):
    """Ensure that we can parse uris correctly."""
    assert Uri.parse(uri) == expected


def test_uri_parse_drive_letter():
    src = "file:///_:/path"
    uri = Uri.parse(src)

    assert uri == Uri.create(scheme="file", path="/_:/path")
    assert uri.fs_path == r"\_:\path" if IS_WIN else "/_:/path"


def test_uri_parse_validation():
    """Ensure that we validate uris when parsing"""

    with pytest.raises(ValueError):
        Uri.parse("file:////shares/files/p.cs")


@pytest.mark.skipif(not IS_WIN, reason="Windows only")
@pytest.mark.parametrize(
    "path, expected_uri, expected_str",
    [
        (
            r"c:\test\drive",
            Uri.create(scheme="file", path="/c:/test/drive"),
            "file:///c%3A/test/drive",
        ),
        (
            r"\\shäres\path\c#\plugin.json",
            Uri.create(scheme="file", authority="shäres", path="/path/c#/plugin.json"),
            "file://sh%C3%A4res/path/c%23/plugin.json",
        ),
        (
            r"\\localhost\c$\GitDevelopment\express",
            Uri.create(
                scheme="file", authority="localhost", path="/c$/GitDevelopment/express"
            ),
            "file://localhost/c%24/GitDevelopment/express",
        ),
        (
            r"c:\test with %\path",
            Uri.create(scheme="file", path="/c:/test with %/path"),
            "file:///c%3A/test%20with%20%25/path",
        ),
        (
            r"c:\test with %25\path",
            Uri.create(scheme="file", path="/c:/test with %25/path"),
            "file:///c%3A/test%20with%20%2525/path",
        ),
        (
            r"c:\test with %25\c#code",
            Uri.create(scheme="file", path="/c:/test with %25/c#code"),
            "file:///c%3A/test%20with%20%2525/c%23code",
        ),
        (
            r"\\shares",
            Uri.create(scheme="file", authority="shares", path="/"),
            "file://shares/",
        ),
        (
            "\\\\shares\\",
            Uri.create(scheme="file", authority="shares", path="/"),
            "file://shares/",
        ),
    ],
)
def test_uri_for_file(path: str, expected_uri: Uri, expected_str: str):
    """Ensure that we can construct a uri for a filepath correctly."""
    uri = Uri.for_file(path)

    assert uri == expected_uri
    assert str(uri) == expected_str


@pytest.mark.parametrize(
    "base, extra, expected",
    [
        ("file:///foo/", "../../bazz", "file:///bazz"),
        ("file:///foo", "../../bazz", "file:///bazz"),
        ("file:///foo/bar", "./bazz", "file:///foo/bar/bazz"),
        ("file:///foo/bar", "bazz", "file:///foo/bar/bazz"),
        ("file:", "bazz", "file:///bazz"),
        ("http://domain", "bazz", "http://domain/bazz"),
        ("https://domain", "bazz", "https://domain/bazz"),
        ("http:", "bazz", "http:/bazz"),
        ("https:", "bazz", "https:/bazz"),
        ("foo:/", "bazz", "foo:/bazz"),
        ("foo://bar/", "bazz", "foo://bar/bazz"),
        pytest.param(
            "file:///c:/foo/",
            "../../bazz",
            "file:///bazz",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "file://server/share/c:/",
            "../../bazz",
            "file://server/bazz",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "file://server/share/c:",
            "../../bazz",
            "file://server/bazz",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "file://ser/foo/",
            "../../bazz",
            "file://ser/bazz",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "file://ser/foo",
            "../../bazz",
            "file://ser/bazz",
            marks=pytest.mark.skipif(IS_WIN, reason="N/A for Windows"),
        ),
        pytest.param(
            "file:///c:/foo/",
            "../../bazz",
            "file:///c:/bazz",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "file://server/share/c:/",
            "../../bazz",
            "file://server/share/bazz",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "file://server/share/c:",
            "../../bazz",
            "file://server/share/bazz",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "file://ser/foo/",
            "../../bazz",
            "file://ser/foo/bazz",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "file://ser/foo",
            "../../bazz",
            "file://ser/foo/bazz",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
        pytest.param(
            "file:///c:/foo/bar",
            "./other/foo.img",
            "file:///c:/foo/bar/other/foo.img",
            marks=pytest.mark.skipif(not IS_WIN, reason="Windows only"),
        ),
    ],
)
def test_uri_join_path(base: str, extra: str, expected):
    """Ensure that we can join uri paths correctly."""

    uri = Uri.parse(base).join(extra)
    assert uri.as_string(encode=False) == expected

    uri2 = Uri.parse(base) / extra
    assert uri2.as_string(encode=False) == expected


@pytest.mark.parametrize(
    "base, extra",
    [("foo:", "bazz"), ("foo://bar", "bazz")],
)
def test_uri_join_path_error(base: str, extra: str):
    """Ensure that we can join uri paths correctly."""

    with pytest.raises(ValueError) as e:
        Uri.parse(base).join(extra)

    assert "has no path" in str(e)

    with pytest.raises(ValueError) as e:
        _ = Uri.parse(base) / extra

    assert "has no path" in str(e)
