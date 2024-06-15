from pydantic import BaseModel


class FileDescriptor(BaseModel):

    f_name: str
    f_url: str
    image: str
    dtc: str
    dtm: str
    size: str
    metadata: dict[str, str]


class FieldSpec(BaseModel):
    id: str
    name: str
    description: str
    dtype: str


class StreamSpec(BaseModel):

    id: str
    name: str
    description: str
    unit: str
    frequency: int
    fields: list[FieldSpec]
    index: list[FieldSpec]
