from typing import Any, Dict, List


class Group:
    description: str
    values: List[str]

    def __init__(
        self,
        description: str,
        values: List[str],
    ) -> None:
        self.description = description
        self.values = values

    @staticmethod
    def create(data: Dict[str, Any]):
        return Group(
            description=str(data["description"]),
            values=[*map(str, data["values"])],
        )
