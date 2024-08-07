import asyncio
import random
import time
from functools import partial, wraps
from typing import Callable

prefix = "d_"


def asyncify(func, executor):
    @wraps(func)
    async def run(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))

    return run


def gen_randseq(length: int = 5) -> str:
    options = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(random.choice(options) for x in range(length))


def init_logging():
    import logging
    import os

    if "jupyter" in os.environ['_']:
        # inside jupyter notebook
        logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]")
    else:
        from rich.logging import RichHandler
        logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])


def identity(x):
    return x


class Enveloper:

    def __init__(
        self,
        *,
        prefix: bytes | None = None,
        transform: Callable | None = None,
        suffix: bytes | None = None,
    ) -> None:
        self.prefix = prefix
        self.transform = transform
        self.suffix = suffix

    def __call__(self, msg):
        if self.transform is not None:
            msg = self.transform(msg)
        if (self.prefix or self.suffix) is not None:
            package = []
            if self.prefix is not None:
                package.append(self.prefix)
            package.append(msg)
            if self.suffix is not None:
                package.append(self.suffix)
            return package
        return msg


def envelope(x, prefix: bytes, suffix: bytes):
    return [prefix, x, suffix]


sleep = time.sleep
