import time


def generate_block(size, num_blocks, seed=0, use_storage=False, set_to_zero=False):
    """
    Generate a square block of given size.
    :param size: <Integer> Block size
    :param num_blocks: <Integer> Number of blocks
    :param seed: <Integer> Random seed
    :param use_storage: <Boolean> If use_storage
    :param set_to_zero: <Boolean> Set block to zeros
    :param psco_name: <String> Persistent object name if use_storage
    :return: Block (persisted if use_storage)
    """
    if use_storage:
        from storage_model_matmul.block import Block

        ret = Block()
        ret.make_persistent()
        ret.generate_block(size, num_blocks, set_to_zero=set_to_zero, seed=seed)
    else:
        from model.block import Block

        ret = Block()
        ret.generate_block(size, num_blocks, set_to_zero=set_to_zero, seed=seed)
    return ret


def main(num_blocks, elems_per_block, check_result, seed, use_storage):
    """
    Matmul main.
    :param num_blocks: <Integer> Number of blocks
    :param elems_per_block: <Integer> Number of elements per block
    :param check_result: <Boolean> Check results against sequential version
                         of matmul
    :param seed: <Integer> Random seed
    :param use_storage: <Boolean> Use storage
    :return: None
    """
    print("Starting application")
    start_time = time.time()

    # Generate the dataset in a distributed manner
    # i.e: avoid having the master a whole matrix
    A, B, C = [], [], []
    matrix_name = ["A", "B"]
    for i in range(num_blocks):
        for l in [A, B, C]:
            l.append([])
        # Keep track of blockId to initialize with different random seeds
        bid = 0
        for j in range(num_blocks):
            for ix, l in enumerate([A, B]):
                psco_name = "%s%02dg%02d" % (matrix_name[ix], i, j)
                l[-1].append(
                    generate_block(
                        elems_per_block, num_blocks, seed=seed + bid, use_storage=use_storage
                    )
                )
                bid += 1
            C[-1].append(
                generate_block(
                    elems_per_block, num_blocks, set_to_zero=True, use_storage=use_storage
                )
            )

    print(A)
    print(B)
    print(C)


def parse_args():
    """
    Arguments parser.
    Code for experimental purposes.
    :return: Parsed arguments.
    """
    import argparse

    description = "Object Oriented COMPSs-PSCO blocked matmul implementation"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-b", "--num_blocks", type=int, default=1, help="Number of blocks (N in NxN)"
    )
    parser.add_argument(
        "-e", "--elems_per_block", type=int, default=2, help="Elements per block (N in NxN)"
    )
    parser.add_argument("--check_result", action="store_true", help="Check obtained result")
    parser.add_argument("--seed", type=int, default=0, help="Pseudo-Random seed")
    parser.add_argument("--use_storage", action="store_true", help="Use storage?")
    return parser.parse_args()


if __name__ == "__main__":
    opts = parse_args()
    main(**vars(opts))
