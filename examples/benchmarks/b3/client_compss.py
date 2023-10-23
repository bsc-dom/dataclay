import time

import numpy as np
from pycompss.api.api import compss_barrier, compss_wait_on
from pycompss.api.parameter import CONCURRENT, IN
from pycompss.api.task import task

from dataclay.contrib.modeltest.classes import Box

# configurations
iterations = 100
mb = 1
num_elements = (mb * 1024 * 1024) // np.dtype(np.int32).itemsize
array = np.empty(num_elements, dtype=np.int32)


@task(box=CONCURRENT)
def make_persistent(box):
    box.make_persistent()


@task(returns=1)
def make_sleep():
    time.sleep(10)
    return 42


@task(box=IN)
def get_box_value(box):
    return box.value


if __name__ == "__main__":
    start_time = time.perf_counter()
    for i in range(500):
        make_sleep()
    compss_barrier()
    end_time = time.perf_counter()
    print(f"Time sleep: {end_time - start_time:0.5f} seconds")

    boxes = []
    start_time = time.perf_counter()
    for i in range(iterations):
        box = Box(i)
        boxes.append(box)
        make_persistent(box)
    compss_barrier()
    end_time = time.perf_counter()
    print(f"Time make_persistent: {end_time - start_time:0.5f} seconds")

    start_time = time.perf_counter()
    for box in boxes:
        get_box_value(box)
    compss_barrier()
    end_time = time.perf_counter()
    print(f"Time read all values: {end_time - start_time:0.5f} seconds")

    # backends = client.get_backends()
    # start_time = time.perf_counter()
    # for backend in backends.values():
    #     backend.flush_all()
    # end_time = time.perf_counter()
    # print(f"Time flush_all: {end_time - start_time:0.5f} seconds")

    # start_time = time.perf_counter()
    # for box in boxes:
    #     box.value
    # end_time = time.perf_counter()
    # print(f"Time load and read all values: {end_time - start_time:0.5f} seconds")
