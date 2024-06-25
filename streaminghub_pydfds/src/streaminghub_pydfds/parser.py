import logging
from typing import Any, Dict

from jsonschema.exceptions import ValidationError
from jsonschema.protocols import Validator
from referencing import Resource
from referencing.jsonschema import DRAFT202012, Schema, SchemaRegistry

from .loader import PathOrURILoader
from .typing import Collection, Node, Stream
from .url import PathOrURL


class Parser:
    """
    Parser for DFDS Metadata

    """

    def __init__(
        self,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.loader = PathOrURILoader()

    def get_stream_metadata(
        self,
        meta_ptr: str,
    ) -> Stream:
        self.logger.debug(f"getting stream metadata: {meta_ptr}")
        metadata = self.fetch_metadata(meta_ptr)
        return Stream(**metadata)

    def get_node_metadata(
        self,
        meta_ptr: str,
    ) -> Node:
        self.logger.debug(f"getting node metadata: {meta_ptr}")
        metadata = self.fetch_metadata(meta_ptr)
        return Node(**metadata)

    def get_collection_metadata(
        self,
        meta_ptr: str,
    ) -> Collection:
        self.logger.debug(f"getting collection metadata: {meta_ptr}")
        metadata = self.fetch_metadata(meta_ptr)
        return Collection(**metadata)

    def fetch_metadata(
        self,
        meta_ptr: str,
    ) -> dict:
        """
        Fetch metadata from a filesystem path or a uri.
        If a schema is present, validate its content against the schema.
        Next, replace all {"$ref$: "<path>"} occurences with their referenced content.

        @param path: filesystem path or uri of the metadata
        @return: validated, deferenced metadata
        """
        meta_ptr_obj = PathOrURL(meta_ptr)

        meta_url = meta_ptr_obj.to_url()
        meta_base = meta_ptr_obj.to_url(drop_fragment=True)

        self.logger.debug(f"resolved url (metadata): {meta_url}")
        metadata = self.loader.get(meta_url)

        # if schema is present, validate against it
        if "$schema" in metadata:
            schema_ptr = metadata["$schema"]
            schema_ptr_obj = PathOrURL(schema_ptr)

            self.logger.debug(f"schema url object: {schema_ptr_obj}")
            # TODO uncomment after fixing SSL issues in validation
            # schema_url = meta_ptr_obj.join(schema_ptr_obj).to_url()
            # self.logger.debug(f"resolved url (schema): {schema_url}")
            # schema = self.loader.get(schema_url)
            # self.validate(metadata, schema, schema_url)

        # recursively update uri-references with actual values
        metadata = self.dereference(metadata, base=meta_base)
        return metadata

    def validate(
        self,
        metadata: dict,
        schema: dict,
        schema_uri: str,
    ) -> None:
        try:
            # new implementation
            self.logger.debug(f"validating metadata against schema: {schema_uri}")
            schema_obj = Resource[Schema](schema, DRAFT202012)
            schema_reg = SchemaRegistry().with_resource(schema_uri, schema_obj)
            validator = Validator(schema_obj, schema_reg)  # type: ignore
            validator.validate(metadata)
            # old implementation
            # resolver = jsonschema.RefResolver(schema_uri, schema)
            # jsonschema.validate(metadata, schema=schema, resolver=resolver)
        except ValidationError as e:
            raise AssertionError(f"metadata does not validate against schema: {schema_uri}")

    def dereference(
        self,
        metadata: Dict[str, Any],
        base: str,
    ) -> Dict[str, Any]:
        # replace @ref with referenced value
        if len(metadata.keys()) == 1 and "@ref" in metadata.keys():
            ref = metadata["@ref"]
            self.logger.debug(f"dereferencing {ref} with base={base}")
            ptr = PathOrURL(base).join(PathOrURL(ref))
            metadata = self.fetch_metadata(ptr.to_url())
            if "device" in metadata:
                metadata = {"device": metadata["device"]}
        else:
            for k, v in metadata.items():
                # avoid circular dereferencing
                if k not in ["node", "@ref"]:
                    if isinstance(v, dict):
                        metadata[k] = self.dereference(v, base)
        return metadata
