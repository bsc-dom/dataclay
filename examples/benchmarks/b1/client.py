import time

from dataclay import Client
from dataclay.contrib.modeltest.classes import Counter

client = Client()
client.start()

iterations = 1000


class BasicCounter:
    def __init__(self):
        self.count = 0

    def inc(self):
        self.count += 1


basic_counter = BasicCounter()
start_time = time.perf_counter()
for _ in range(iterations):
    basic_counter.inc()
end_time = time.perf_counter()
print(f"Time basic counter: {end_time - start_time:0.5f} seconds")

local_counter = Counter()
start_time = time.perf_counter()
for _ in range(iterations):
    local_counter.inc()
end_time = time.perf_counter()
print(f"Time local counter: {end_time - start_time:0.5f} seconds")

persistent_counter = Counter()
persistent_counter.make_persistent()
start_time = time.perf_counter()
for _ in range(iterations):
    persistent_counter.inc()
end_time = time.perf_counter()
print(f"Time persistent counter: {end_time - start_time:0.5f} seconds")
