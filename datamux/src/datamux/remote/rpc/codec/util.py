from functools import singledispatch
from typing import Any

import numpy as np


@singledispatch
def to_serializable(val: Any) -> Any:
    """Used by default."""
    return str(val)


@to_serializable.register(np.float32)
def ts_float32(val: np.float32):
    """Used if *val* is an instance of numpy.float32."""
    return np.float64(val)
