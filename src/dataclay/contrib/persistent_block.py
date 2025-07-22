from __future__ import annotations

import numpy as np
from sklearn.metrics import pairwise_distances

from dataclay import DataClayObject, activemethod
from dataclay.event_loop import run_dc_coroutine

try:
    from pycompss.api.task import task
    from pycompss.api.parameter import IN
except ImportError:
    from dataclay.contrib.dummy_pycompss import task, IN


class PersistentBlock(DataClayObject):
    block_data: np.ndarray
    shape: tuple[int, ...]
    ndim: int
    nbytes: int
    itemsize: int
    size: int

    @activemethod
    def __init__(self, data: np.ndarray):
        self.block_data = data
        self.shape = data.shape
        self.ndim = data.ndim
        self.size = data.size
        self.itemsize = data.itemsize
        self.nbytes = data.nbytes

    @activemethod
    def __getitem__(self, key) -> np.ndarray:
        return self.block_data[key]

    @activemethod
    def __setitem__(self, key, value):
        self.block_data[key] = value

    @activemethod
    def __delitem__(self, key):
        del self.block_data[key]

    @activemethod
    def __array__(self) -> np.ndarray:
        return self.block_data

    @activemethod
    def transpose(self) -> np.ndarray:
        return self.block_data.transpose()

    @activemethod
    def __len__(self) -> int:
        return len(self.block_data)

    @task(target_direction=IN)
    @activemethod
    def rotate_in_place(self, rotation_matrix: np.ndarray):
        self.block_data = self.block_data @ rotation_matrix

    @task(target_direction=IN, returns=object)
    @activemethod
    def partial_sum(self, centers: np.ndarray) -> np.ndarray:
        partials = np.zeros((centers.shape[0], 2), dtype=object)
        arr = self.block_data
        close_centers = pairwise_distances(arr, centers).argmin(axis=1)
        for center_idx in range(len(centers)):
            indices = np.argwhere(close_centers == center_idx).flatten()
            partials[center_idx][0] = np.sum(arr[indices], axis=0)
            partials[center_idx][1] = indices.shape[0]
        return partials

    @task(target_direction=IN, returns=np.ndarray)
    @activemethod
    def partial_histogram(self, n_bins: int, n_dimensions: int) -> np.ndarray:
        values, _ = np.histogramdd(self.block_data, n_bins, [(0, 1)] * n_dimensions)
        return values
