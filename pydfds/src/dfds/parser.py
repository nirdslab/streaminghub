import json
import logging
import os
from typing import Any, Dict, Tuple, TypeVar
from urllib.parse import ParseResult, urlparse, urljoin
from urllib.request import urlopen

import jsonschema
import jsonschema.validators
from dtypes import Collection, Source, Stream, Transform


class SchemaMismatchError(BaseException):
    pass


class NoSchemaError(BaseException):
    pass


class FileDecodeError(BaseException):
    pass


logger = logging.getLogger()

T = TypeVar("T", Collection, Stream, Source, Transform)


def parse_ref(
    ref: str,
) -> Tuple[str, str]:
    ref_obj: ParseResult = urlparse(ref)
    ref_fspath = ""
    ref_uri = ""
    if ref_obj.scheme == "" and ref_obj.netloc == "":
        ref_fspath = ref_obj.path
    else:
        ref_uri = f"{ref_obj.scheme}//{ref_obj.netloc}{ref_obj.path}"
    return ref_fspath, ref_uri


def resolve_path(
    ref: str,
    base: str = "",
) -> str:
    # parse ref
    (ref_fspath, ref_uri) = parse_ref(ref)

    if len(base) == 0:
        return ref_uri or os.path.abspath(ref_fspath)

    # parse base
    (base_fspath, base_uri) = parse_ref(base)

    if bool(base_uri):
        return urljoin(base_uri, ref_uri or ref_fspath)

    if bool(base_fspath) and bool(ref_fspath):
        return os.path.join(os.path.dirname(base_fspath), ref_fspath)

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
    content: dict

    # fetch resource
    logger.debug(f"Fetching: {path}...")
    with fn(path) as payload:
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
) -> None:
    try:
        jsonschema.validate(
            instance=metadata,
            schema=schema,
            cls=jsonschema.validators.Draft202012Validator,
        )
    except jsonschema.ValidationError as e:
        raise SchemaMismatchError(e)


def resolve_metadata_refs(
    metadata: Dict[str, Any],
    base: str,
) -> Dict[str, Any]:
    if len(metadata.keys()) == 1 and "@ref" in metadata.keys():
        ref_uri = resolve_path(metadata["@ref"], base)
        logging.debug(f"resolved ref path: {ref_uri}")
        input()
        metadata = fetch_and_validate_metadata(ref_uri)
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
    metadata = fetch(ref)

    # if schema is present, validate against it
    if "$schema" in metadata:
        schema_uri = resolve_path(metadata["$schema"], ref)
        logging.debug(f"resolved schema path: {schema_uri}")
        input()
        schema = fetch(schema_uri)
        validate_metadata_against_schema(
            metadata=metadata,
            schema=schema,
        )

    # recursively update uri-references with actual values
    metadata = resolve_metadata_refs(
        metadata=metadata,
        base=ref,
    )

    return metadata


def get_metadata(ref: str, type: T) -> T:
    path = resolve_path(ref)
    logging.debug(f"resolved metadata path: {path}")
    input()
    metadata = fetch_and_validate_metadata(path)
    return type.create(metadata)


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    metadata = get_metadata(
        ref="../../../dfds/samples/running_metrics.collection.json",
        type=type(Collection),
    )
