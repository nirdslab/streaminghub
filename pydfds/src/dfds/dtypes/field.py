from typing import Dict, Type

import numpy as np


class Field:
    name: str
    description: str
    dtype: type

    __dtypes_map: Dict[str, Type] = {
        "f16": np.float16,
        "f32": np.float32,
        "f64": np.float64,
        "i8": np.int8,
        "i16": np.int16,
        "i32": np.int32,
        "u8": np.uint8,
        "u16": np.uint16,
        "u32": np.uint32,
    }

    def __init__(
        self,
        name: str,
        description: str,
        dtype: type,
    ) -> None:
        self.name = name
        self.description = description
        self.dtype = dtype

    @staticmethod
    def create(
        data: Dict[str, str],
    ):
        return Field(
            name=data["name"],
            description=data["description"],
            dtype=Field.__dtypes_map[data["dtype"]],
        )
