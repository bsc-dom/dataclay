class DataClayObjectMetaData(object):


    def __init__(self, tags_to_oids, tags_to_class_ids, tags_to_hints, num_refs_pointing_to_obj):
        self.tags_to_oids = tags_to_oids
        self.tags_to_class_ids = tags_to_class_ids
        self.tags_to_hints = tags_to_hints
        self.num_refs_pointing_to_obj = num_refs_pointing_to_obj

    def modify_hints(self, hints_mapping):
        """
        Modify hints associated to oids provided with ee id provided
        :param hints_mapping: dict of oid -> new hint
        """
        for tag, oid in self.tags_to_oids.items():
            if oid in hints_mapping:
                new_hint = hints_mapping[oid]
                self.tags_to_hints[tag] = new_hint


