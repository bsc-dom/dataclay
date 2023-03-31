import argparse

import numpy as np

# Using argparse, read the number of matrices ,the size of the matrices and the path to the folder
parser = argparse.ArgumentParser(description="Matrix Generator")
parser.add_argument("--matrices", type=int, default=5, help="Number of matrices")
parser.add_argument("--size", type=int, default=100, help="Size of matrices")
parser.add_argument("--path", type=str, default="./data/", help="Path to the folder")
args = parser.parse_args()

for i in range(args.matrices):
    matrix = np.random.random((args.size, args.size))
    np.save(f"{args.path}/matrix-{i+1:02}.npy", matrix)
