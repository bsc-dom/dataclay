import numpy as np

# from pycompss.api.task import task


class Block(object):

    def __init__(self, block=None):
        self.block = block

    def generate_block(self, size, num_blocks, seed=0, set_to_zero=False):
        """
        Generate a square block of given size.
        :param size: <Integer> Block size
        :param num_blocks: <Integer> Number of blocks
        :param seed: <Integer> Random seed
        :param set_to_zero: <Boolean> Set block to zeros
        :return: None
        """
        np.random.seed(seed)
        if not set_to_zero:
            b = np.random.random((size, size))
            # Normalize matrix to ensure more numerical precision
            b /= np.sum(b) * float(num_blocks)
        else:
            b = np.zeros((size, size))
        self.block = b

    # @task()
    def fused_multiply_add(self, a, b):
        """Accumulate a product.

        This FMA operation multiplies the two operands (parameters a and b) and
        accumulates its result onto self.

        Note that the multiplication is the matrix multiplication (aka np.dot)
        """
        self.block += np.dot(a.block, b.block)
