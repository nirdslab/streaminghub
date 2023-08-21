import io
import json
import logging
from typing import Tuple

import avro
import avro.datafile
import avro.io
import avro.schema

from .serializer import Serializer


class AvroSerializer(Serializer):
    """
    Serialization Utilty for DataMux

    """

    schema_registry = {}
    blank_schema = {
        "type": "record",
        "namespace": "streaminghub",
        "name": "data",
        "fields": [],
    }
    type_map = {
        bool: "boolean",
        int: "int",
        float: "float",
        bytes: "bytes",
        str: "string",
    }

    def avro_preprocess(
        self,
        content: dict,
    ) -> dict:
        flat_dict = {}
        for root_k in content.keys():
            for inner_k, v in content[root_k].items():
                flat_dict[f"{root_k}.{inner_k}"] = v
        return flat_dict

    def avro_postprocess(
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

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> list[bytes]:
        logging.debug(f"encode(): topic={topic}, content={content}")
        lines = []
        if len(content) == 0:
            content_enc = b""
        elif topic.startswith(b"data"):
            # preprocessing
            content = self.avro_preprocess(content)
            # register schema + add to payload
            if topic not in self.schema_registry:
                schema = self.__create_schema(content)
                self.bind_schema(topic, schema)
                schema_enc = self.__encode_json(schema)
                lines.append(b"schema_" + topic + b"||" + schema_enc)
            # avro-encode
            content_enc = self.__encode_avro(topic, content)
        else:
            # json-encode
            content_enc = self.__encode_json(content)
        lines.append(topic + b"||" + content_enc)
        return lines

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict]:
        logging.debug(f"decode(): payload={payload}")
        topic, content_enc = payload.split(b"||", maxsplit=1)
        content = {}
        if len(content_enc) == 0:
            pass
        elif topic.startswith(b"data"):
            # schema must be registered before running decode_avro()
            assert topic in self.schema_registry, f"decode_avro(): no registered schema for topic={topic}"
            schema = self.schema_registry[topic]
            content = self.__decode_avro(content_enc, schema)
            # postprocessing
            content = self.avro_postprocess(content)
        else:
            # decode using json backend
            content = self.__decode_json(content_enc)
        return topic, content

    def bind_schema(
        self,
        topic: bytes,
        schema: dict,
    ) -> None:
        self.schema_registry[topic] = avro.schema.make_avsc_object(schema)

    def __create_schema(
        self,
        content: dict,
    ) -> dict:
        schemadict = self.blank_schema.copy()
        for k, v in content.items():
            schemadict["fields"].append(
                {
                    "name": k,
                    "type": self.type_map[type(v)],
                    "doc": "...",
                }
            )
        return schemadict

    def __encode_avro(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        # schema must be registered before running encode_avro()
        assert topic in self.schema_registry, f"encode_avro(): no registered schema for topic={topic}"
        # get schema
        schema = self.schema_registry[topic]
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
        return dict(content) # type: ignore

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
