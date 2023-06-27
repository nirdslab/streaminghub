import h5py
import numpy as np

if __name__ == "__main__":
    # open dataset
    filename = "/path/to/h5/file"
    file = h5py.File(name=filename, mode="r")

    # get single recording from dataset
    recording = file.get("P3_N0_Q1")
    assert isinstance(recording, h5py.Dataset)

    # read recording into numpy array
    data = np.array(recording)

    input(data)
