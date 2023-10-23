import time

from pycompss.api.api import compss_barrier
from pycompss.api.parameter import CONCURRENT, INOUT
from pycompss.api.task import task

from dataclay.contrib.modeltest.classes import Counter

# from dataclay.contrib.modeltest.compss import Counter


iterations = 1000


@task(counter=CONCURRENT)
def counter_inc(counter):
    counter.inc()


@task(returns=1)
def make_sleep():
    time.sleep(10)
    return 42


if __name__ == "__main__":
    start_time = time.perf_counter()
    for i in range(500):
        make_sleep()
    compss_barrier()
    end_time = time.perf_counter()
    print(f"Time sleep: {end_time - start_time:0.5f} seconds")

    counter = Counter()
    counter.make_persistent()
    start_time = time.perf_counter()
    for _ in range(iterations):
        # counter.inc()
        counter_inc(counter)

    compss_barrier()
    end_time = time.perf_counter()
    print(f"Time persistent counter: {end_time - start_time:0.5f} seconds")
