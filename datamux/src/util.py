import asyncio
from functools import wraps, partial
from typing import Dict, Any, Generator

DICT = Dict[str, Any]
DICT_GENERATOR = Generator[DICT, None, None]


def asyncify(func, executor):
  @wraps(func)
  async def run(*args, **kwargs):
    return asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))

  return run
