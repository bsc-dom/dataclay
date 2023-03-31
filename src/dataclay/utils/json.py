import json
from uuid import UUID


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


# OPTIMIZE: This adds an extra function call and might impact performance.
#           To change how json handles UUID we can create a custome py_make_scanner
#           It may not be worth the complexity.
def uuid_parser(obj):
    for key in obj:
        try:
            if isinstance(obj[key], str):
                obj[key] = UUID(obj[key])
            elif isinstance(obj[key], list):
                obj[key] = list(map(UUID, obj[key]))
        except Exception:
            pass
    return obj
