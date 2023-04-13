from typing import Any, Dict

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

    @staticmethod
    def create(
        data: Dict[str, Any],
    ):
        return Stream(
            name=str(data["name"]),
            description=str(data["description"]),
            unit=str(data["unit"]),
            frequency=float(data["frequency"]),
            fields={k: Field.create(v) for k, v in dict.items(data["fields"])},
            index={k: Field.create(v) for k, v in dict.items(data["index"])},
        )
