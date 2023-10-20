import time
from dataclay.contrib.modeltest.classes import Box
from pycompss.api.task import task
from pycompss.api.parameter import CONCURRENT, IN
from pycompss.api.api import compss_wait_on, compss_barrier


iterations = 100000


@task(i=IN, returns=1)
def box_maker(i):
    box = Box(i)
    box.make_persistent()
    return box


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
        boxes.append(box_maker(i))
    boxes = compss_wait_on(boxes)
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
