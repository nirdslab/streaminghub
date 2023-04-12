from typing import Any, Dict


class Author:
    name: str
    affiliation: str
    email: str

    def __init__(
        self,
        name: str,
        affiliation: str,
        email: str,
    ) -> None:
        self.name = name
        self.affiliation = affiliation
        self.email = email

    @staticmethod
    def create(data: Dict[str, Any]):
        return Author(
            name=str(data["name"]),
            affiliation=str(data["affiliation"]),
            email=str(data["email"]),
        )
