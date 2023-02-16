import argparse
import concurrent.futures
import time
from multiprocessing import Lock
from threading import Thread

import dataclay

print_lock = Lock()

# Function to sum all the matrix
def sum_matrices(matrices):

    # NOTE: It should not be needed in future versions
    from model.matrix import Matrix

    matrix_sum = Matrix()
    matrix_sum.init_zeros(matrices[0].shape)
    for matrix in matrices:
        matrix_sum += matrix
    return matrix_sum


def read_matrix(id, matrices, path):

    # NOTE: It should not be needed in future versions
    from model.matrix import Matrix

    matrix = Matrix()
    matrix.make_persistent()
    matrix.read_matrix(f"{path}/matrix-{(id%5)+1:02}.npy")
    matrices.append(matrix)


def print_times(times, num_matrices, num_sums):
    with print_lock:
        print("Number of matrices:", num_matrices)
        print("Total time:", times[-1] - times[0])
        if num_matrices > 0:
            print("Read time:", times[1] - times[0])
        if num_sums > 0:
            print("Sum time:")
            for i in range(2, len(times)):
                print(f"\tSum {i-1}:", times[i] - times[i - 1])


def multithread_main(num_matrices, num_sums, path):

    # This should become before using registered classes
    client = dataclay.client(username="testuser", password="s3cret", dataset="testuser")
    client.start()

    # This uses registered classes
    from model.matrix import Matrix

    times = [time.time()]

    # Read matrix from folder
    threads = []
    matrices = []
    for i in range(num_matrices):
        t = Thread(target=read_matrix, args=(i, matrices, path))
        t.start()
        threads.append(t)

    # Wait all threads to finish
    for t in threads:
        t.join()

    times.append(time.time())

    # Sum all the matrix "num_sums" times
    for _ in range(num_sums):
        sum_matrices(matrices)
        times.append(time.time())

    # Print execution time
    print_times(times, num_matrices, num_sums)


if __name__ == "__main__":

    # Parsing input parameters
    parser = argparse.ArgumentParser(description="Matrix Operations")
    parser.add_argument("num_matrices", type=int, help="Number of matrices to be read")
    parser.add_argument("num_sums", type=int, help="Number of sums to perform")
    parser.add_argument("--processes", type=int, default=1, help="Number of executions")
    parser.add_argument("--path", type=str, default="./data/", help="Path to the folder")

    args = parser.parse_args()

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for _ in range(args.processes):
            executor.submit(multithread_main, args.num_matrices, args.num_sums, args.path)

    # finish()
