from __future__ import annotations

import time

import numpy as np

try:
    from pycompss.api.parameter import CONCURRENT, INOUT
    from pycompss.api.task import task
except ImportError:
    from dataclay.contrib.dummy_pycompss import task, INOUT, CONCURRENT

from dataclay import DataClayObject, activemethod


class Block(DataClayObject):
    submatrix: np.ndarray

    def __init__(self, submatrix: np.ndarray):
        self.submatrix = submatrix

    @task(target_direction=INOUT)
    @activemethod
    def imuladd(self, a: Block, b: Block):
        """Perform an in-place fused multiply-addition operation.

        This FMA operation can be described as: self += a * b.
        """
        self.submatrix += a.submatrix @ b.submatrix


class Matrix(DataClayObject):
    num_blocks: int
    blocksize: int
    size: int
    blocks: list[list[Block]]

    def __init__(self, n: int):
        # 1024 will be our blocksize
        self.blocksize = 1024
        self.num_blocks = n // 1024
        self.size = n

        # Start uninitialized
        self.blocks = list()

    @activemethod
    def random(self):
        for i in range(self.num_blocks):
            row = list()
            self.blocks.append(row)
            for j in range(self.num_blocks):
                b = Block(np.random.random((self.blocksize, self.blocksize)))
                b.make_persistent()
                row.append(b)

    @activemethod
    def zeros(self):
        for i in range(self.num_blocks):
            row = list()
            self.blocks.append(row)
            for j in range(self.num_blocks):
                b = Block(np.zeros((self.blocksize, self.blocksize)))
                b.make_persistent()
                row.append(b)

    @activemethod
    def ones(self):
        for i in range(self.num_blocks):
            row = list()
            self.blocks.append(row)
            for j in range(self.num_blocks):
                b = Block(np.ones((self.blocksize, self.blocksize)))
                b.make_persistent()
                row.append(b)

    def __matmul__(self, other: Matrix) -> Matrix:
        # Initialize the output matrix with zeros
        result = Matrix(self.size)
        result.zeros()
        result.make_persistent()

        result_blocks = result.blocks

        # Evaluate the output by doing fused multiply-add operations on result
        for i in range(self.num_blocks):
            for k in range(self.num_blocks):
                for j in range(self.num_blocks):
                    result_blocks[i][j].imuladd(self.blocks[i][k], other.blocks[k][j])

        # Wait for consolidation on all blocks
        from pycompss.api.api import compss_wait_on

        for i in range(self.num_blocks):
            for j in range(self.num_blocks):
                result_blocks[i][j] = compss_wait_on(result_blocks[i][j])
        # Update the result blocks
        result.blocks = result_blocks
        return result


class Counter(DataClayObject):
    count: int

    def __init__(self):
        self.count = 0

    @task(target_direction=CONCURRENT)
    @activemethod
    def inc(self):
        self.count += 1


class CPUIntensiveTask(DataClayObject):

    matrix1: np.ndarray
    matrix2: np.ndarray

    def __init__(self, size=5000):
        self.matrix1 = np.random.rand(size, size)
        self.matrix2 = np.random.rand(size, size)

    @activemethod
    async def a_cpu_intensive_task(self):
        result = np.dot(self.matrix1, self.matrix2)
        return result

    @activemethod
    def cpu_intensive_task(self):
        result = np.dot(self.matrix1, self.matrix2)
        return result
