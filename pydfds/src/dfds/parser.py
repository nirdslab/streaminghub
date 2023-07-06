import json
import logging
import os
from typing import Any, Dict, Tuple
from urllib.parse import ParseResult, urljoin, urlparse
from urllib.request import urlopen

import jsonschema

from .typing import Collection, Node, Stream

logger = logging.getLogger()


class Parser:
    """
    Parser for DFDS Metadata

    """

    def __parse_ref(
        self,
        ref: str,
    ) -> Tuple[str, str, str]:
        ref_obj: ParseResult = urlparse(ref)
        ref_fspath = ""
        ref_uri = ""
        if ref_obj.scheme == "" and ref_obj.netloc == "":
            ref_fspath = ref_obj.path
        else:
            ref_uri = f"{ref_obj.scheme}://{ref_obj.netloc}{ref_obj.path}"
        return ref_fspath, ref_uri, ref_obj.fragment

    def __resolve_path(
        self,
        ref: str,
        base: str = "",
    ) -> str:
        # parse ref
        (ref_fspath, ref_uri, ref_fragment) = self.__parse_ref(ref)
        if len(ref_fragment) > 0:
            ref_fragment = "#" + ref_fragment
        if ref_uri:
            return ref_uri + ref_fragment
        assert len(ref_fspath) > 0
        if len(base) == 0:
            return os.path.abspath(ref_fspath) + ref_fragment
        # parse base
        (base_fspath, base_uri, _) = self.__parse_ref(base)
        if base_uri:
            return urljoin(base_uri, ref_fspath) + ref_fragment
        if base_fspath:
            return (
                os.path.abspath(os.path.join(os.path.dirname(base_fspath), ref_fspath))
                + ref_fragment
            )
        else:
            raise ValueError()

    def __fetch(
        self,
        path: str,
    ) -> dict:
        """
        Fetch a resource from the given path

        @param ref: a path (filesystem/uri)
        @return: content of the resource
        """

        path_obj: ParseResult = urlparse(path)
        if path_obj.scheme == "" and path_obj.netloc == "":
            fn, fn_path = open, path_obj.path
        else:
            fn, fn_path = urlopen, path
        content: dict

        # fetch resource
        with fn(fn_path) as payload:
            try:
                content = json.load(payload)
                logger.debug(f"Fetched: {path}")
            except json.JSONDecodeError:
                raise Exception("")

        # navigate to the fragment, if any
        fragment = content
        if len(path_obj.fragment) > 0:
            for part in filter(None, path_obj.fragment.split("/")):
                fragment = fragment[part]
            fragment["@node"] = {"@ref": fn_path}

        # return content
        return fragment

    def __validate_metadata_against_schema(
        self,
        metadata: dict,
        schema: dict,
        schema_uri: str,
    ) -> None:
        try:
            resolver = jsonschema.RefResolver(schema_uri, schema)
            jsonschema.validate(
                instance=metadata,
                schema=schema,
                resolver=resolver,
            )
        except jsonschema.ValidationError as e:
            raise AssertionError("Metadata does not validate against its schema")

    def __resolve_metadata_refs(
        self,
        metadata: Dict[str, Any],
        base: str,
    ) -> Dict[str, Any]:
        if len(metadata.keys()) == 1 and "@ref" in metadata.keys():
            path = self.__resolve_path(metadata["@ref"], base)
            logging.debug(f"resolved ref path: {path}")
            metadata = self.__fetch_and_validate_metadata(path)
            # special case: if node, drop circular references (inputs, outputs)
            if "device" in metadata:
                metadata = {"device": metadata["device"]}
        else:
            for k, v in metadata.items():
                if isinstance(v, dict):
                    metadata[k] = self.__resolve_metadata_refs(v, base)
        return metadata

    def __fetch_and_validate_metadata(
        self,
        ref: str,
    ) -> dict:
        """
        Fetch metadata from a filesystem path or a uri.
        If a schema is present, validate its content against the schema.
        Next, replace all {"$ref$: "<path>"} occurences with their referenced content.

        @param ref: filesystem path or uri of the metadata
        @return: validated, deferenced metadata
        """
        ref = self.__resolve_path(ref)
        logging.debug(f"resolved metadata path: {ref}")
        metadata = self.__fetch(ref)

        # if schema is present, validate against it
        if "$schema" in metadata:
            schema_uri = self.__resolve_path(metadata["$schema"], ref)
            logging.debug(f"resolved schema path: {schema_uri}")
            schema = self.__fetch(schema_uri)
            self.__validate_metadata_against_schema(
                metadata=metadata,
                schema=schema,
                schema_uri=schema_uri,
            )

        # recursively update uri-references with actual values
        metadata = self.__resolve_metadata_refs(
            metadata=metadata,
            base=ref,
        )
        return metadata

    def get_stream_metadata(
        self,
        path: str,
    ) -> Stream:
        logging.debug(f"getting stream metadata: {path}")
        metadata = self.__fetch_and_validate_metadata(path)
        return Stream(**metadata)

    def get_node_metadata(
        self,
        path: str,
    ) -> Node:
        logging.debug(f"getting node metadata: {path}")
        metadata = self.__fetch_and_validate_metadata(path)
        return Node(**metadata)

    def get_collection_metadata(
        self,
        path: str,
    ) -> Collection:
        logging.debug(f"getting collection metadata: {path}")
        metadata = self.__fetch_and_validate_metadata(path)
        return Collection(**metadata)
