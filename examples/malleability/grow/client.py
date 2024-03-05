from dataclay import Client
from dataclay.contrib.modeltest.classes import Box

client = Client()
client.start()

boxes = []

print("\nStarting client application...")

# Creating and persisting 100 Box instances.
for i in range(100):
    box = Box(i)
    box.make_persistent()
    boxes.append(box)
print("All Box instances persisted successfully.")

# Flushing all data from the backends of DataClay.
backends = client.get_backends()
for backend in backends.values():
    backend.flush_all()
print("All data flushed successfully.")

# Reading the value of each Box instance after flushing.
for i, box in enumerate(boxes):
    assert box.value == i
print("All values read successfully.")

print("Client application finished successfully.\n")
