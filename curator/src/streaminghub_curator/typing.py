from pydantic import BaseModel

class FileDescriptor(BaseModel):

    f_name: str
    f_url: str
    image: str
    dtc: str
    dtm: str
    size: str
    metadata: dict[str, str]