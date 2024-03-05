import time

import numpy as np

from dataclay import Client
from dataclay.contrib.modeltest.classes import Box

client = Client(host="localhost", username="testuser", password="s3cret", dataset="testdata")
client.start()

# configurations
iterations = 100
mb = 1
num_elements = (mb * 1024 * 1024) // np.dtype(np.int32).itemsize
array = np.empty(num_elements, dtype=np.int32)

boxes = []
start_time = time.perf_counter()
for _ in range(iterations):
    box = Box(array)
    box.make_persistent()
    boxes.append(box)
end_time = time.perf_counter()
print(f"Time make_persistent: {end_time - start_time:0.5f} seconds")

start_time = time.perf_counter()
for box in boxes:
    box.value
end_time = time.perf_counter()
print(f"Time read all values: {end_time - start_time:0.5f} seconds")

backends = client.get_backends()
start_time = time.perf_counter()
for backend in backends.values():
    backend.flush_all()
end_time = time.perf_counter()
print(f"Time flush_all: {end_time - start_time:0.5f} seconds")

start_time = time.perf_counter()
for box in boxes:
    box.value
end_time = time.perf_counter()
print(f"Time load and read all values: {end_time - start_time:0.5f} seconds")
