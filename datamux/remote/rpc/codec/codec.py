from abc import ABC, abstractmethod
import logging
from typing import Tuple


class Codec(ABC):
    """
    Base Class for Serialization / Deserialization

    """

    def __init__(
        self,
    ):
        self.logger = logging.getLogger(__name__)
        self.active = False

    @abstractmethod
    def encode(
        self,
        topic: bytes,
        content: dict,
    ) -> bytes | list[bytes]:
        raise NotImplementedError()

    @abstractmethod
    def decode(
        self,
        payload: bytes,
    ) -> Tuple[bytes, dict] | None:
        raise NotImplementedError()
