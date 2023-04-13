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
