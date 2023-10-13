import time
from dataclay.contrib.modeltest.classes import Box
from dataclay import Client

import cProfile

pr = cProfile.Profile()

# client = Client(username="testuser", password="s3cret", dataset="testdata")
client = Client(host="localhost", username="testuser", password="s3cret", dataset="testdata")
client.start()

iterations = 1000
pr.enable()
boxes = []
start_time = time.perf_counter()
for i in range(iterations):
    box = Box(i)
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
