import time

from dataclay import Client
from dataclay.contrib.modeltest.classes import Box
from dataclay.event_loop import run_dc_coroutine

client = Client()
client.start()

# Number of Box instances to create and manipulate.
iterations = 100_000
boxes = []

# Start timing the creation and persistence of Box instances.
start_time = time.perf_counter()
for i in range(iterations):
    box = Box(i)
    box.make_persistent()
    boxes.append(box)
end_time = time.perf_counter()
print(f"Time make_persistent: {end_time - start_time:0.5f} seconds")

# Timing for reading the value attribute of each Box instance.
start_time = time.perf_counter()
for box in boxes:
    box.value
end_time = time.perf_counter()
print(f"Time read all values: {end_time - start_time:0.5f} seconds")

# Flushing all data from the backends of DataClay.
backends = client.get_backends()
start_time = time.perf_counter()
for backend in backends.values():
    run_dc_coroutine(backend.flush_all)
end_time = time.perf_counter()
print(f"Time flush_all: {end_time - start_time:0.5f} seconds")

# Timing for loading and reading the value of each Box instance after flushing.
start_time = time.perf_counter()
for box in boxes:
    box.value
end_time = time.perf_counter()
print(f"Time load and read all values: {end_time - start_time:0.5f} seconds")
