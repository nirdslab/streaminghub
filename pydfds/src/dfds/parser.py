import json
import logging
import os
from typing import Any, Dict, Tuple, TypeVar
from urllib.parse import ParseResult, urljoin, urlparse
from urllib.request import urlopen

import jsonschema
import jsonschema.validators
from dtypes import Collection, Source, Stream, Pipe


class SchemaMismatchError(BaseException):
    pass


class NoSchemaError(BaseException):
    pass


class FileDecodeError(BaseException):
    pass


logger = logging.getLogger()


def parse_ref(
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


def resolve_path(
    ref: str,
    base: str = "",
) -> str:
    # parse ref
    (ref_fspath, ref_uri, ref_fragment) = parse_ref(ref)

    if len(ref_fragment) > 0:
        ref_fragment = "#" + ref_fragment

    if ref_uri:
        return ref_uri + ref_fragment

    assert len(ref_fspath) > 0

    if len(base) == 0:
        return os.path.abspath(ref_fspath) + ref_fragment

    # parse base
    (base_fspath, base_uri, _) = parse_ref(base)

    if base_uri:
        return urljoin(base_uri, ref_fspath) + ref_fragment

    if base_fspath:
        return (
            os.path.abspath(os.path.join(os.path.dirname(base_fspath), ref_fspath))
            + ref_fragment
        )

    else:
        raise ValueError()


def fetch(
    path: str,
) -> dict:
    """
    Fetch a resource from the given path

    @param ref: a path (filesystem/uri)
    @return: content of the resource
    """

    path_obj: ParseResult = urlparse(path)
    is_path_fs = path_obj.scheme == "" and path_obj.netloc == ""
    fn = open if is_path_fs else urlopen
    fn_path = path_obj.path if is_path_fs else path
    content: dict

    # fetch resource
    with fn(fn_path) as payload:
        try:
            content = json.load(payload)
            logger.debug(f"Fetched: {path}")
        except json.JSONDecodeError:
            raise FileDecodeError()

    # navigate to the fragment, if any
    if len(path_obj.fragment) > 0:
        for part in filter(None, path_obj.fragment.split("/")):
            content = content[part]

    # return content
    return content


def validate_metadata_against_schema(
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
        raise SchemaMismatchError(e)


def resolve_metadata_refs(
    metadata: Dict[str, Any],
    base: str,
) -> Dict[str, Any]:
    if len(metadata.keys()) == 1 and "@ref" in metadata.keys():
        path = resolve_path(metadata["@ref"], base)
        logging.debug(f"resolved ref path: {path}")
        metadata = fetch_and_validate_metadata(path)
    else:
        for k, v in metadata.items():
            if isinstance(v, dict):
                metadata[k] = resolve_metadata_refs(v, base)
    return metadata


def fetch_and_validate_metadata(
    ref: str,
) -> dict:
    """
    Fetch metadata from a filesystem path or a uri.
    If a schema is present, validate its content against the schema.
    Next, replace all {"$ref$: "<path>"} occurences with their referenced content.

    @param ref: filesystem path or uri of the metadata
    @return: validated, deferenced metadata
    """
    ref = resolve_path(ref)
    logging.debug(f"resolved metadata path: {ref}")
    metadata = fetch(ref)

    # if schema is present, validate against it
    if "$schema" in metadata:
        schema_uri = resolve_path(metadata["$schema"], ref)
        logging.debug(f"resolved schema path: {schema_uri}")
        schema = fetch(schema_uri)
        validate_metadata_against_schema(
            metadata=metadata,
            schema=schema,
            schema_uri=schema_uri,
        )

    # recursively update uri-references with actual values
    metadata = resolve_metadata_refs(
        metadata=metadata,
        base=ref,
    )
    return metadata


def get_collection_metadata(path: str) -> Collection:
    logging.debug(f"getting collection metadata: {path}")
    metadata = fetch_and_validate_metadata(path)
    return Collection.create(metadata)


def get_stream_metadata(path: str) -> Stream:
    logging.debug(f"getting stream metadata: {path}")
    metadata = fetch_and_validate_metadata(path)
    return Stream.create(metadata)


def get_source_metadata(path: str) -> Source:
    logging.debug(f"getting source metadata: {path}")
    metadata = fetch_and_validate_metadata(path)
    return Source.create(metadata)


def get_pipe_metadata(path: str) -> Pipe:
    logging.debug(f"getting pipe metadata: {path}")
    metadata = fetch_and_validate_metadata(path)
    return Pipe.create(metadata)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    metadata = get_collection_metadata(
        "../../../dfds/samples/running_metrics.collection.json"
    )
