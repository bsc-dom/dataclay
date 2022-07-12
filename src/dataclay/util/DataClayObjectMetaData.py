class DataClayObjectMetaData(object):
    def __init__(
        self,
        alias,
        is_read_only,
        tags_to_oids,
        tags_to_class_ids,
        tags_to_hints,
        num_refs_pointing_to_obj,
        orig_object_id,
        root_location,
        origin_location,
        replica_locations,
    ):
        self.alias = alias
        self.is_read_only = is_read_only
        self.tags_to_oids = tags_to_oids
        self.tags_to_class_ids = tags_to_class_ids
        self.tags_to_hints = tags_to_hints
        self.num_refs_pointing_to_obj = num_refs_pointing_to_obj
        self.orig_object_id = orig_object_id
        self.root_location = root_location
        self.origin_location = origin_location
        # IMPORTANT: clone to avoid modifications of metadata affect already serialized objects
        self.replica_locations = list()
        if replica_locations is not None:
            for loc in replica_locations:
                self.replica_locations.append(loc)

    def modify_hints(self, hints_mapping):
        """
        Modify hints associated to oids provided with ee id provided
        :param hints_mapping: dict of oid -> new hint
        """
        for tag, oid in self.tags_to_oids.items():
            if oid in hints_mapping:
                new_hint = hints_mapping[oid]
                self.tags_to_hints[tag] = new_hint

    def __str__(self):
        return (
            f"[tags_to_oids={self.tags_to_oids}, tags_to_class_ids={self.tags_to_class_ids} "
            f"is_read_only={self.is_read_only}, orig_object_id={self.orig_object_id}, "
            f"root_location={self.root_location}, origin_location={self.origin_location}, "
            f"alias={self.alias}, replica_locations={self.replica_locations}]"
        )
