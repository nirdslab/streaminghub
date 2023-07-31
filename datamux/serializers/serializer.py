import io
import json
from typing import Tuple

import avro
import avro.datafile
import avro.io
import avro.schema


avro_schemas: dict[str, avro.schema.RecordSchema] = {}


def get_avro_schema(
    topic: bytes,
    content: dict | None = None,
) -> avro.schema.RecordSchema:
    name = f"datamux.{topic.decode()}"
    if name not in avro_schemas:
        assert content is not None
        fields = [dict(name=k, type=type(v).__name__) for k,v in content.items()]
        avro_schemas["name"] = avro.schema.RecordSchema(
            name=name,
            namespace="streaminghub",
            fields=fields
        )
    return avro_schemas["name"]

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
            content_enc = self.encode_fn(topic, content)
        payload = topic + b"|" + content_enc
        return payload

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict]:
        topic, content_enc = payload.split(b"|", maxsplit=1)
        content = {}
        if len(content_enc) > 0:
            content = self.decode_fn(topic, content_enc)
        return topic, content

    def __encode_avro(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes:
        schema = get_avro_schema(topic, content)
        buffer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(buffer)
        self.writer.write_record(schema, content, encoder) # type: ignore
        content_bytes = buffer.getvalue()
        return content_bytes

    def __decode_avro(
        self,
        topic: bytes,
        content_bytes: bytes,
    ) -> dict:
        schema = get_avro_schema(topic)
        buffer = io.BytesIO(content_bytes)
        decoder = avro.io.BinaryDecoder(buffer)
        content = self.reader.read_record(schema, schema, decoder)
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
