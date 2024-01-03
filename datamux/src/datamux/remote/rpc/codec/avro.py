import io
import json
import logging
from typing import Tuple

import avro
import avro.datafile
import avro.io
import avro.schema

from .codec import Codec

prefix = b"d_"


class AvroCodec(Codec):
    """
    Avro Codec

    """

    logger = logging.getLogger(__name__)
    schema_cache_max_n = 1000
    __blank_schema = {
        "type": "record",
        "namespace": "streaminghub.datamux.data",
        "name": None,
        "fields": None,
    }
    __type_map = {
        bool: "boolean",
        int: "int",
        float: "float",
        bytes: "bytes",
        str: "string",
    }

    def __init__(self) -> None:
        self.__schema_registry = {}

    def __create_schema(
        self,
        subtopic: bytes,
        content: dict,
    ) -> dict:
        schemadict = self.__blank_schema.copy()
        schemadict["name"] = subtopic.decode()
        schemadict["fields"] = []
        for k, v in content.items():
            schemadict["fields"].append(
                {
                    "name": k,
                    "type": self.__type_map[type(v)],
                    "doc": "...",
                }
            )
        return schemadict

    def __preprocess(
        self,
        content: dict,
    ) -> dict:
        flat_dict = {}
        for root_k in content.keys():
            for inner_k, v in content[root_k].items():
                flat_dict[f"{root_k}.{inner_k}"] = v
        return flat_dict

    def __postprocess(
        self,
        content: dict,
    ) -> dict:
        nested_dict = {}
        for flat_k, v in content.items():
            root_k, inner_k = flat_k.split(".", 1)
            if root_k not in nested_dict:
                nested_dict[root_k] = {}
            nested_dict[root_k][inner_k] = v
        return nested_dict

    def __cache_schema(
        self,
        subtopic: bytes,
        schema: avro.schema.Schema,
    ) -> None:
        self.__schema_registry[subtopic] = schema
        # silently prune cache
        N = self.schema_cache_max_n
        for key in list(self.__schema_registry)[:-N]:
            self.__schema_registry.pop(key, None)

    def __encode_avro(
        self,
        subtopic: bytes,
        content: dict,
    ) -> bytes:
        # get schema
        schema = self.__schema_registry[subtopic]
        writer = avro.io.DatumWriter(schema)
        # encoding
        buffer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(buffer)
        writer.write(content, encoder)
        content_bytes = buffer.getvalue()
        # return encoded data
        return content_bytes

    def __decode_avro(
        self,
        content_bytes: bytes,
        schema: avro.schema.Schema,
    ) -> dict:
        # create reader
        reader = avro.io.DatumReader(schema)
        # decoding
        buffer = io.BytesIO(content_bytes)
        decoder = avro.io.BinaryDecoder(buffer)
        content = reader.read(decoder)
        # return decoded data
        return dict(content)  # type: ignore

    def __encode_json(
        self,
        content: dict,
    ) -> bytes:
        content_str = json.dumps(content)
        content_bytes = content_str.encode()
        return content_bytes

    def __decode_json(
        self,
        content_bytes: bytes,
    ) -> dict:
        content_str = content_bytes.decode()
        content = json.loads(content_str)
        return content

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> list[bytes]:
        self.logger.debug(f"encode(): topic={topic}, content={content}")
        lines = []
        if len(content) == 0:
            self.logger.info(f"encode(): got empty message - topic={topic}")
            content_enc = b""
            lines.append(topic + b"||" + content_enc)
        elif topic.startswith(prefix) and len(content) > 0:
            # preprocessing
            subtopic = topic[len(prefix) :]
            content = self.__preprocess(content)
            # ensure schema is registered
            if subtopic not in self.__schema_registry:
                # create schema
                schema = self.__create_schema(subtopic, content)
                # register schema in __schema_registry
                self.__cache_schema(subtopic, avro.schema.make_avsc_object(schema))
                self.logger.debug(f"encode(): assigned schema - subtopic={subtopic}")
                # json-encode schema
                schema_enc = self.__encode_json(schema)
                # write encoded schema to output
                lines.append(b"schema_" + subtopic + b"||" + schema_enc)
                self.logger.debug(f"encode(): wrote schema to payload - subtopic={subtopic}")
            # avro-encode content
            content_enc = self.__encode_avro(subtopic, content)
            # write encoded content to output
            lines.append(prefix + subtopic + b"||" + content_enc)
        else:
            # json-encode content
            content_enc = self.__encode_json(content)
            # write encoded content to output
            lines.append(topic + b"||" + content_enc)
        return lines

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict] | None:
        self.logger.debug(f"decode(): payload={payload}")
        topic, content_enc = payload.split(b"||", maxsplit=1)

        if len(content_enc) == 0:
            self.logger.info(f"decode(): got empty message - topic={topic}")
            return topic, {}
        elif topic.startswith(b"schema_"):
            subtopic = topic[7:]
            schema = self.__decode_json(content_enc)
            self.logger.debug(f"decode(): read schema from payload - subtopic={subtopic}")
            self.__cache_schema(subtopic, avro.schema.make_avsc_object(schema))
            self.logger.debug(f"decode(): assigned schema - subtopic={subtopic}")
            return None
        elif topic.startswith(prefix):
            subtopic = topic[len(prefix) :]
            if subtopic not in self.__schema_registry:
                self.logger.error(f"decode(): no schema - subtopic={subtopic}")
                return None
            schema = self.__schema_registry[subtopic]
            content = self.__decode_avro(content_enc, schema)
            # postprocessing
            content = self.__postprocess(content)
            return topic, content
        else:
            # decode using json backend
            content = self.__decode_json(content_enc)
            return topic, content
