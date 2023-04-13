from typing import List


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
