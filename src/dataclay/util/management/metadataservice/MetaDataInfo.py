class MetaDataInfo(object):
    def __init__(self, id, is_read_only, dataset_name, metaclass_id, locations, alias, owner_id):
        self.id = id
        self.is_read_only = is_read_only
        self.dataset_name = dataset_name
        self.metaclass_id = metaclass_id
        self.locations = locations
        self.alias = alias
        self.owner_id = owner_id

    def __str__(self):
        return (
            f"[id={self.id}, is_read_only={self.is_read_only}, dataset_name={self.dataset_name}, "
            f"metaclass_id={self.metaclass_id}, locations={self.locations}, "
            f"alias={self.alias}, owner_id={self.owner_id}]"
        )
