class Field:
    name: str
    description: str
    dtype: type

    def __init__(
        self,
        name: str,
        description: str,
        dtype: type,
    ) -> None:
        self.name = name
        self.description = description
        self.dtype = dtype
