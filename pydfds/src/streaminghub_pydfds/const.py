import numpy as np

# from metadata to dtypes
dtype_map_fwd = {
    "f16": np.float16,
    "f32": np.float32,
    "f64": np.float64,
    "i8": np.int8,
    "i16": np.int16,
    "i32": np.int32,
    "u8": np.uint8,
    "u16": np.uint16,
    "u32": np.uint32,
    "bytes": np.dtype("O"),
}

# from dtypes to metadata
dtype_map_inv = {
    np.dtype("float16"): "f16",
    np.dtype("float32"): "f32",
    np.dtype("float64"): "f64",
    np.dtype("int8"): "i8",
    np.dtype("int16"): "i16",
    np.dtype("int32"): "i32",
    np.dtype("uint8"): "u8",
    np.dtype("uint16"): "u16",
    np.dtype("uint32"): "u32",
    np.dtype("O"): "bytes",
}
