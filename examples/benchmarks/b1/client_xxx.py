import time
from dataclay.contrib.modeltest.classes import Counter
from dataclay import Client

# client = Client(username="testuser", password="s3cret", dataset="testdata")
client = Client(host="localhost", username="testuser", password="s3cret", dataset="testdata")
client.start()

start_time = time.perf_counter()
for _ in range(1000):
    client.get_backends()
end_time = time.perf_counter()
print(f"Time basic counter: {end_time - start_time:0.5f} seconds")


