from unittest.mock import MagicMock
# Store original __import__
orig_import = __import__
def import_mock(name, *args):
    print(f"-- Mocking module {name}")
    if name == 'dataclay.api':
        # tested module
        return orig_import(name, *args)
    else:
        return MagicMock()
