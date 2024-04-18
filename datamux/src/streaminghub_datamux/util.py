import asyncio
import random
from functools import partial, wraps


def asyncify(func, executor):
    @wraps(func)
    async def run(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))

    return run


def gen_randseq(length: int = 5) -> str:
    options = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "".join(random.choice(options) for x in range(length))
