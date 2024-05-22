from uuid import UUID

from aiorwlock import RWLock


class LockManager:
    def __init__(self):
        self.locks: dict[UUID, RWLock] = {}

    def get_lock(self, object_id):
        if object_id not in self.locks:
            # Create a new lock if it does not exist
            self.locks[object_id] = RWLock()
        return self.locks[object_id]


lock_manager = LockManager()


# Example usage
# async def access_object(object_id, manager, operation="read"):
#     lock = manager.get_lock(object_id)
#     if operation == "read":
#         async with lock.reader_lock:
#             # Perform read operation
#             print(f"Reading from object {object_id}")
#             await asyncio.sleep(1)  # Simulate read delay
#     elif operation == "write":
#         async with lock.writer_lock:
#             # Perform write operation
#             print(f"Writing to object {object_id}")
#             await asyncio.sleep(1)  # Simulate write delay


# async def main():
#     manager = LockManager()
#     # Simulate concurrent access
#     await asyncio.gather(
#         access_object("obj1", manager, "read"),
#         access_object("obj1", manager, "write"),
#         access_object("obj2", manager, "read"),
#         access_object("obj1", manager, "read"),
#         access_object("obj2", manager, "write"),
#     )
