from dataclay import DataClayObject, activemethod
import numpy as np

try:
    from pycompss.api.task import task
    from pycompss.api.parameter import CONCURRENT
except ImportError:
    from dataclay.contrib.dummy_pycompss import task, CONCURRENT


class Block(DataClayObject):
    block: np.ndarray

    def __init__(self, block=None):
        super(Block, self).__init__()
        self.block = block

    @activemethod
    def generate_block(
        self, size: int, num_blocks: int, seed: int = 0, set_to_zero: bool = False
    ) -> None:
        """
        Generate a square block of given size.
        :param size: Block size
        :param num_blocks: Number of blocks
        :param seed: Random seed
        :param set_to_zero: Set block to zeros
        """
        np.random.seed(seed)
        if not set_to_zero:
            b = np.random.random((size, size))
            # Normalize matrix to ensure more numerical precision
            b /= np.sum(b) * float(num_blocks)
        else:
            b = np.zeros((size, size))
        self.block = b

    @task(target_direction=CONCURRENT)
    @activemethod
    def fused_multiply_add(self, a: "Block", b: "Block") -> None:
        """Accumulate a product.

        This FMA operation multiplies the two operands (parameters a and b) and
        accumulates its result onto self.

        Note that the multiplication is the matrix multiplication (aka np.dot)
        """
        self.block += np.dot(a.block, b.block)
