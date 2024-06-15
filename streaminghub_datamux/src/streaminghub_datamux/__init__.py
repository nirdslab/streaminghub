from .typing import *
from .util import *


def init():
    import logging

    from rich.logging import RichHandler

    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])


from .transforms import *
from .api import API
from .remote.api import RemoteAPI