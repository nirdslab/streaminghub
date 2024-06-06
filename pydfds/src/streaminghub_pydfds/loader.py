import json
import logging
from urllib.request import urlopen

from .url import PathOrURL


class PathOrURILoader:
    """
    Get a resource from the given path

    """

    def get(
        self,
        ptr: str,
    ) -> dict:
        self.logger = logging.getLogger(__name__)
        obj = PathOrURL(ptr)

        if obj.has_fspath():
            fn, path = open, obj.fspath
        else:
            fn, path = urlopen, obj.urlpath

        # fetch resource
        content: dict
        with fn(path) as payload:
            try:
                content = json.load(payload)
                self.logger.debug(f"Fetched: {path}")
            except json.JSONDecodeError:
                raise Exception("")

        # navigate to the fragment, if any
        fragment = content
        if obj.has_fragment():
            for part in filter(None, obj.fragment.split("/")):
                fragment = fragment[part]
            fragment["node"] = {"@ref": path}

        # return content
        return fragment
