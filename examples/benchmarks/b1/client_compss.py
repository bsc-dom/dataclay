import time
from dataclay.contrib.modeltest.classes import Counter

# from dataclay.contrib.modeltest.compss import Counter

from pycompss.api.task import task
from pycompss.api.parameter import CONCURRENT, INOUT
from pycompss.api.api import compss_barrier


iterations = 1000


@task(counter=CONCURRENT)
def counter_inc(counter):
    counter.inc()


counter = Counter()
counter.make_persistent()
start_time = time.perf_counter()
for _ in range(iterations):
    # counter.inc()
    counter_inc(counter)

compss_barrier()
end_time = time.perf_counter()
print(f"Time persistent counter: {end_time - start_time:0.5f} seconds")
