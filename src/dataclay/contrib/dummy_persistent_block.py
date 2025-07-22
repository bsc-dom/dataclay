class PersistentBlock:
    """
    Dummy PersistentBlock class for testing purposes.
    This class does not implement any functionality and is used to avoid
    import errors when the actual PersistentBlock is not available.
    """

    def __init__(self, data=None):
        self.block_data = data if data is not None else []
        self.shape = ()
        self.ndim = 0
        self.size = 0
        self.itemsize = 0
        self.nbytes = 0

    def __getitem__(self, key):
        return self.block_data[key]

    def __setitem__(self, key, value):
        self.block_data[key] = value

    def __delitem__(self, key):
        del self.block_data[key]

    def __array__(self):
        return self.block_data

    def transpose(self):
        return self.block_data

    def __len__(self):
        return len(self.block_data)
