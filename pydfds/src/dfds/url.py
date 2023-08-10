from __future__ import annotations

import logging
from copy import copy
from urllib.parse import urljoin, urlparse

logger = logging.getLogger()


class PathOrURL:
    """
    Common object for both file paths and URLs

    """

    def __init__(self, ptr: str) -> None:
        logging.debug(f"Parsing ptr='{ptr}'")
        url = urlparse(ptr)
        logging.debug(f"parsed ptr='{ptr}': scheme='{url.scheme}', netloc='{url.netloc}', path='{url.path}', fragment='{url.fragment}'")

        fspath = ""
        urlpath = ""
        sep = ""
        frag = url.fragment.strip()

        if len(url.scheme) == 1:
            # got a windows file path
            logging.debug(f"ptr={ptr} appears to be windows path")
            sep = "/"
            fspath = ptr[: ptr.index(":") + 1] + url.path.strip()
        elif url.scheme == "" and url.netloc == "":
            # got a unix file path
            logging.debug(f"ptr={ptr} appears to be unix path")
            sep = "/"
            fspath = url.path.strip()
        else:
            # got a url
            logging.debug(f"ptr={ptr} appears to be url")
            urlpath = f"{url.scheme}://{url.netloc}{url.path}".strip()

        self.fspath = fspath.rstrip(sep)
        self.urlpath = urlpath.rstrip("/")
        self.fragment = frag.lstrip("#")
        self.sep = sep

    def __str__(self) -> str:
        return f"Path (fs='{self.fspath}', url='{self.urlpath}', fragment='{self.fragment}', sep='{self.sep}')"

    def is_empty(self) -> bool:
        return not (self.has_fspath() or self.has_urlpath() or self.has_fragment())

    def has_fspath(self) -> bool:
        return len(self.fspath) > 0

    def has_urlpath(self) -> bool:
        return len(self.urlpath) > 0

    def has_fragment(self) -> bool:
        return len(self.fragment) > 0

    def join(self, ptr: PathOrURL) -> PathOrURL:
        logging.info(f"Trying to join {self} and {ptr}")
        assert not self.has_fragment()

        if ptr.has_urlpath():
            # ptr with url overrides self
            obj = copy(ptr)
        else:
            # join self and ptr
            obj = copy(self)
            if obj.has_fspath():
                i = obj.fspath.rindex(obj.sep)
                assert i > 0
                prefix = obj.fspath[: i + 1]
                suffix = obj.fspath[i + 1 :]
                obj.fspath = prefix + urljoin(suffix, ptr.fspath)
            if obj.has_urlpath():
                obj.urlpath = urljoin(obj.urlpath, ptr.fspath)
            obj.fragment = ptr.fragment

        return obj

    def __to_url(
        self,
    ) -> str:
        if self.has_urlpath():
            assert not self.has_fspath()
            return self.urlpath
        if self.has_fspath():
            assert not self.has_urlpath()
            return self.fspath
        raise ValueError()

    def to_url(
        self,
        drop_fragment: bool = False,
    ) -> str:
        url = self.__to_url()
        if not drop_fragment and self.has_fragment():
            url += "#" + self.fragment
        return url
