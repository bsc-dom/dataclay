from dataclay import Client
from dataclay.contrib.modeltest.classes import Box

client = Client()
client.start()

boxes = []
backends = client.get_backends()
backend_instances = {}

for backend_id in backends:
    backend_instances[backend_id] = 0

print("\nStarting client application...")

# Creating and persisting 100 Box instances.
for i in range(100):
    box = Box(i)
    box.make_persistent()
    boxes.append(box)
    backend_instances[box._dc_meta.master_backend_id] += 1
print("All Box instances persisted successfully.")

# Printing the number of instances in each backend.
for backend_id in backend_instances:
    print(f"Backend {backend_id} has {backend_instances[backend_id]} instances.")

# Flushing all data from the backends of DataClay.
for backend in backends.values():
    backend.flush_all()
print("All data flushed successfully.")

# Reading the value of each Box instance after flushing.
for i, box in enumerate(boxes):
    assert box.value == i
print("All values read successfully.")

print("Client application finished successfully.\n")
