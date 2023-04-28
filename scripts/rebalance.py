import dataclay
from dataclay.metadata.api import MetadataAPI

client = dataclay.Client(
    host="127.0.0.1", username="testuser", password="s3cret", dataset="testuser"
)
client.start()

backends = client.get_backends()

metadata_api = MetadataAPI("127.0.0.1", 6379)
dc_objects = metadata_api.get_all_objects()
num_objects = len(dc_objects)
mean = num_objects // len(backends)

print("Num backends:", len(backends))
print("Num objects:", num_objects)
print("Mean:", mean)

backends_objects = {backend_id: [] for backend_id in backends.keys()}
for object_md in dc_objects.values():
    backends_objects[object_md.backend_id].append(object_md.id)

print("\nBefore rebalance:")
backends_diff = dict()
for backend_id, objects in backends_objects.items():
    print(f"{backend_id}: {len(objects)}")
    diff = len(objects) - mean
    backends_diff[backend_id] = diff

for backend_id, object_ids in backends_objects.items():
    if backends_diff[backend_id] <= 0:
        continue
    for new_backend_id in backends_objects.keys():
        if backend_id == new_backend_id or backends_diff[new_backend_id] >= 0:
            continue
        while backends_diff[backend_id] > 0 and backends_diff[new_backend_id] < 0:
            object_id = object_ids.pop()
            backend_client = backends[backend_id]
            backend_client.move_object(object_id, new_backend_id, None)
            backends_diff[backend_id] -= 1
            backends_diff[new_backend_id] += 1


print("\nAfter rebalance:")
for backend_id, diff in backends_diff.items():
    print(f"{backend_id}: {mean+diff}")
