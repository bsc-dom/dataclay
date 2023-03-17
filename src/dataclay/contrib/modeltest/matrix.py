from typing import Any

import numpy as np

from dataclay import DataClayObject, activemethod


class Matrix(DataClayObject):

    mtx: np.ndarray
    shape: tuple

    @activemethod
    def init_zeros(self, shape: tuple):
        self.mtx = np.zeros(shape)
        self.shape = shape

    @activemethod
    def init_random(self, shape: tuple):
        self.mtx = np.random.random(shape)
        self.shape = shape

    @activemethod
    def read_matrix(self, file: str):
        with open(file, "rb") as f:
            self.mtx = np.load(f)
            self.shape = self.mtx.shape

    @activemethod
    def __str__(self) -> str:
        return str(self.mtx)

    @activemethod
    def __add__(self, other: Any) -> "Matrix":
        tmp = Matrix()
        if isinstance(other, Matrix):
            tmp.mtx = self.mtx + other.mtx
        else:
            tmp.mtx = self.mtx + other
        return tmp

    @activemethod
    def __iadd__(self, other: Any) -> "Matrix":
        if isinstance(other, Matrix):
            self.mtx += other.mtx
        else:
            self.mtx += other
        return self
