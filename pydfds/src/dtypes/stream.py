from typing import Dict

from .field import Field


class Stream:
    name: str
    description: str
    unit: str
    frequency: float
    fields: Dict[str, Field]
    index: Dict[str, Field]

    def __init__(
        self,
        name: str,
        description: str,
        unit: str,
        frequency: float,
        fields: Dict[str, Field],
        index: Dict[str, Field],
    ) -> None:
        self.name = name
        self.description = description
        self.unit = unit
        self.frequency = frequency
        self.fields = fields
        self.index = index
