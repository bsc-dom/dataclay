import time
from dataclay.contrib.modeltest.classes import Box
from pycompss.api.task import task
from pycompss.api.parameter import CONCURRENT
from pycompss.api.api import compss_wait_on, compss_barrier

iterations = 1000


@task(box=CONCURRENT)
def make_persistent(box):
    box.make_persistent()


boxes = []
start_time = time.perf_counter()
for i in range(iterations):
    box = Box(i)
    boxes.append(box)
    make_persistent(box)
compss_barrier()
end_time = time.perf_counter()
print(f"Time make_persistent: {end_time - start_time:0.5f} seconds")


@task(box=CONCURRENT)
def get_box_value(box):
    return box.value


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
