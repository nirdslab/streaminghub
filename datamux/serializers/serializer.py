import io
import json
from typing import Tuple

import avro
import avro.datafile
import avro.io
import avro.schema

avro_def = {
    "type": "record",
    "namespace": "Data",
    "name": "datapofloat_schema",
    "fields": [
        {"name": "t", "type": "float", "doc": "Column t"},
        {"name": "x", "type": "float", "doc": "Column x"},
        {"name": "y", "type": "float", "doc": "column y"},
        {"name": "dL", "type": "float", "doc": "Column dL"},
        {"name": "dR", "type": "float", "doc": "Column dR"},
        {"name": "aoi", "type": "float", "doc": "Column aoi"},
    ],
}


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
            content_enc = self.encode_fn(content)
        payload = topic + b"|" + content_enc
        return payload

    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict]:
        topic, content_enc = payload.split(b"|", maxsplit=1)
        content = {}
        if len(content_enc) > 0:
            content = self.decode_fn(content_enc)
        return topic, content

    def __encode_avro(
        self,
        content: dict,
    ) -> bytes:
        data = [content]
        schema = avro.schema.make_avsc_object(avro_def)
        buffer = io.BytesIO()
        avro.datafil
        encoder = avro.io.BinaryEncoder(buffer)
        self.writer.write(schema, content, encoder)
        content_bytes = buffer.getvalue()
        return content_bytes

    def __decode_avro(
        self,
        content_bytes: bytes,
    ) -> dict:
        raise NotImplementedError()

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
