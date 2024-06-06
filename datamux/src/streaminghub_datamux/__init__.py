from .typing import *


def init():
    import logging

    from rich.logging import RichHandler

    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])


from .api import API
from .remote.api import RemoteAPI
from .util import *
