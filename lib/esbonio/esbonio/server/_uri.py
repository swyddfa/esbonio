import os.path
import pathlib
import re
from typing import Callable
from typing import Optional
from typing import Union
from urllib import parse

import attrs
from pygls import IS_WIN
from pygls.uris import urlparse

SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z\d+.-]*$")
RE_DRIVE_LETTER_PATH = re.compile(r"^(\/?)([a-zA-Z]:)")


# TODO: Look into upstreaming this into pygls
#       - if it works out
#       - when pygls drops 3.7 (Uri uses the := operator)
@attrs.define(frozen=True)
class Uri:
    """Helper class for working with URIs."""

    scheme: str

    authority: str

    path: str

    query: str

    fragment: str

    def __attrs_post_init__(self):
        """Basic validation."""
        if self.scheme is None:
            raise ValueError("URIs must have a scheme")

        if not SCHEME.match(self.scheme):
            raise ValueError("Invalid scheme")

        if self.authority and self.path and (not self.path.startswith("/")):
            raise ValueError("Paths with an authority must start with a slash '/'")

        if self.path and self.path.startswith("//") and (not self.authority):
            raise ValueError(
                "Paths without an authority cannot start with two slashes '//'"
            )

    def __fspath__(self):
        """Return the file system representation of this uri.

        This makes Uri instances compatible with any function that expects an
        ``os.PathLike`` object!
        """
        # TODO: Should we raise an exception if scheme != "file"?
        return self.as_fs_path(preserve_case=True)

    def __str__(self):
        return self.as_string()

    def __truediv__(self, other):
        return self.join(other)

    @classmethod
    def create(
        cls,
        *,
        scheme: str = "",
        authority: str = "",
        path: str = "",
        query: str = "",
        fragment: str = "",
    ) -> "Uri":
        """Create a uri with the given attributes."""

        if scheme in {"http", "https", "file"}:
            if not path.startswith("/"):
                path = f"/{path}"

        return cls(
            scheme=scheme,
            authority=authority,
            path=path,
            query=query,
            fragment=fragment,
        )

    @classmethod
    def parse(cls, uri: str) -> "Uri":
        """Parse the given uri from its string representation."""
        scheme, authority, path, _, query, fragment = urlparse(uri)
        return cls.create(
            scheme=scheme,
            authority=authority,
            path=path,
            query=query,
            fragment=fragment,
        )

    def resolve(self) -> "Uri":
        """Return the fully resolved version of this Uri."""

        # This operation only makes sense for file uris
        if self.scheme != "file":
            return Uri.parse(str(self))

        return Uri.for_file(pathlib.Path(self).resolve())

    @classmethod
    def for_file(cls, filepath: Union[str, "os.PathLike[str]"]) -> "Uri":
        """Create a uri based on the given filepath."""

        fpath = os.fspath(filepath)
        if IS_WIN:
            fpath = fpath.replace("\\", "/")

        if fpath.startswith("//"):
            authority, *path = fpath[2:].split("/")
            fpath = "/".join(path)
        else:
            authority = ""

        return cls.create(scheme="file", authority=authority, path=fpath)

    @property
    def fs_path(self) -> Optional[str]:
        """Return the equivalent fs path."""
        return self.as_fs_path()

    def where(self, **kwargs) -> "Uri":
        """Return an transformed version of this uri where certain components of the uri
        have been replace with the given arguments.

        Passing a value of ``None`` will remove the given component entirely.
        """
        keys = {"scheme", "authority", "path", "query", "fragment"}
        valid_keys = keys.copy() & kwargs.keys()

        current = {k: getattr(self, k) for k in keys}
        replacements = {k: kwargs[k] for k in valid_keys}

        return Uri.create(**{**current, **replacements})

    def join(self, path: str) -> "Uri":
        """Join this Uri's path component with the given path and return the resulting
        uri.

        Parameters
        ----------
        path
           The path segment to join

        Returns
        -------
        Uri
           The resulting uri
        """

        if not self.path:
            raise ValueError("This uri has no path")

        if IS_WIN:
            fs_path = self.fs_path
            if fs_path is None:
                raise ValueError("Unable to join paths, fs_path is None")

            joined = os.path.normpath(os.path.join(fs_path, path))
            new_path = self.for_file(joined).path
        else:
            new_path = os.path.normpath(os.path.join(self.path, path))

        return self.where(path=new_path)

    def as_fs_path(self, preserve_case: bool = False) -> Optional[str]:
        """Return the file system path correspondin with this uri."""
        if self.path:
            path = _normalize_path(self.path, preserve_case)

            if self.authority and len(path) > 1:
                path = f"//{self.authority}{path}"

            # Remove the leading `/` from windows paths
            elif RE_DRIVE_LETTER_PATH.match(path):
                path = path[1:]

            if IS_WIN:
                path = path.replace("/", "\\")

            return path

        return None

    def as_string(self, encode=True) -> str:
        """Return a string representation of this Uri.

        Parameters
        ----------
        encode
           If ``True`` (the default), encode any special characters.

        Returns
        -------
        str
           The string representation of the Uri
        """

        # See: https://github.com/python/mypy/issues/10740
        encoder: Callable[[str], str] = parse.quote if encode else _replace_chars  # type: ignore[assignment]

        if authority := self.authority:
            usercred, *auth = authority.split("@")
            if len(auth) > 0:
                *user, cred = usercred.split(":")
                if len(user) > 0:
                    usercred = encoder(":".join(user)) + f":{encoder(cred)}"
                else:
                    usercred = encoder(usercred)
                authority = "@".join(auth)
            else:
                usercred = ""

            authority = authority.lower()
            *auth, port = authority.split(":")
            if len(auth) > 0:
                authority = encoder(":".join(auth)) + f":{port}"
            else:
                authority = encoder(authority)

            if usercred:
                authority = f"{usercred}@{authority}"

        scheme_separator = ""
        if authority or self.scheme == "file":
            scheme_separator = "//"

        if path := self.path:
            path = encoder(_normalize_path(path))

        if query := self.query:
            query = encoder(query)

        if fragment := self.fragment:
            fragment = encoder(fragment)

        parts = [
            f"{self.scheme}:",
            scheme_separator,
            authority if authority else "",
            path if path else "",
            f"?{query}" if query else "",
            f"#{fragment}" if fragment else "",
        ]
        return "".join(parts)


def _replace_chars(segment: str) -> str:
    """Replace a certain subset of characters in a uri segment"""
    return segment.replace("#", "%23").replace("?", "%3F")


def _normalize_path(path: str, preserve_case: bool = False) -> str:
    """Normalise the path segment of a Uri.

    Parameters
    ----------
    path
       The path to normalise.

    preserve_case
       If ``True``, preserve the case of the drive label on Windows.
       If ``False``, the drive label will be lowercased.

    Returns
    -------
    str
       The normalised path.
    """

    # normalize to fwd-slashes on windows,
    # on other systems bwd-slashes are valid
    # filename character, eg /f\oo/ba\r.txt
    if IS_WIN:
        path = path.replace("\\", "/")

    # Normalize drive paths to lower case
    if (not preserve_case) and (match := RE_DRIVE_LETTER_PATH.match(path)):
        path = match.group(1) + match.group(2).lower() + path[match.end() :]

    return path
