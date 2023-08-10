import io
import json
from typing import Tuple

import avro
import avro.datafile
import avro.io
import avro.schema


avro_schemas: dict[bytes, avro.schema.RecordSchema] = {}

type_map = {
    bool: "boolean",
    int: "int",
    float: "float",
    bytes: "bytes",
    str: "string",
}


def get_avro_schema(
    topic: bytes,
    content: dict | None,
) -> avro.schema.RecordSchema:
    if topic in avro_schemas:
        return avro_schemas[topic]
    else:
        raise NotImplementedError()


class Serializer:
    def __init__(
        self,
        backend: str,
    ) -> None:
        self.backend = backend
        if self.backend == "json":
            self.encode_fn = self.__encode_json
            self.decode_fn = self.__decode_json
        elif self.backend == "avro":
            self.encode_fn = self.__encode_avro
            self.decode_fn = self.__decode_avro
            self.writer = avro.io.DatumWriter()
            self.reader = avro.io.DatumReader()
        else:
            raise NotImplementedError()

    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        if len(content) == 0:
            content_enc = b""
        else:
            if topic.startswith(b"data"):
                # encode using chosen backend
                content_enc = self.encode_fn(topic, content)
            else:
                # encode using json backend
                content_enc = self.__encode_json(topic, content)
        payload = topic + b"||" + content_enc
        return payload

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict]:
        topic, content_enc = payload.split(b"||", maxsplit=1)
        content = {}
        if len(content_enc) > 0:
            if topic.startswith(b"data"):
                # decode using chosen backend
                content = self.decode_fn(topic, content_enc)
            else:
                # decode using json backend
                content = self.__decode_json(topic, content_enc)
        return topic, content

    def __encode_avro(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        return self.__encode_json(topic, content)
        # fix and implement below
        schema = get_avro_schema(topic, content)
        buffer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(buffer)
        index = content["index"]
        value = content["value"]
        self.writer.write_record(schema, dict(**index, **value), encoder)  # type: ignore
        content_bytes = buffer.getvalue()
        return content_bytes

    def __decode_avro(
        self,
        topic: bytes,
        content_bytes: bytes,
    ) -> dict:
        return self.__decode_json(topic, content_bytes)
        # fix and implement below
        schema = get_avro_schema(topic, None)
        assert schema is not None
        buffer = io.BytesIO(content_bytes)
        print("created buffer")
        decoder = avro.io.BinaryDecoder(buffer)
        print("created decoder")
        content = self.reader.read_record(schema, schema, decoder)
        print("decoder content")
        return dict(content)

    def __encode_json(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        content_str = json.dumps(content)
        content_bytes = content_str.encode()
        return content_bytes

    def __decode_json(
        self,
        topic: bytes,
        content_bytes: bytes,
    ) -> dict:
        content_str = content_bytes.decode()
        content = json.loads(content_str)
        return content
