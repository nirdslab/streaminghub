import logging
from abc import ABC, abstractmethod


class RpcCodec(ABC):
    """
    Base Class for RPC Codec

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
    ) -> bytes | list[bytes]: ...

    @abstractmethod
    def decode(
        self,
        payload: bytes,
    ) -> tuple[bytes, dict] | None: ...
