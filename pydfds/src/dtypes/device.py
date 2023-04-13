class Device:
    model: str
    manufacturer: str
    category: str

    def __init__(
        self,
        model: str,
        manufacturer: str,
        category: str,
    ) -> None:
        self.model = model
        self.manufacturer = manufacturer
        self.category = category
