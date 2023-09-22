# This file should be used with PyCOMPSs
# (typically, through an enqueue_compss command)

from dataclay.contrib.modeltest.compss import Matrix

if __name__ == "__main__":
    # Random generation of 3072 x 3072 matrices
    a = Matrix(3072)
    b = Matrix(3072)
    # Initialize the two matrices with random numbers
    a.random()
    b.random()
    # Make them persistent
    a.make_persistent()
    b.make_persistent()

    print(
        """
*****************************************************
Ready to start the multiplication
*****************************************************
"""
    )

    c = a @ b

    print(
        """
*****************************************************
Multiplication finished
*****************************************************
"""
    )
