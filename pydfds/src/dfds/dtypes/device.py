from typing import Any, Dict, Optional


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

    @staticmethod
    def create(
        data: Optional[Dict[str, Any]],
    ):
        if data is None:
            return None
        return Device(
            model=str(data["model"]),
            manufacturer=str(data["manufacturer"]),
            category=str(data["category"]),
        )
