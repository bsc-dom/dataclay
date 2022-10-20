class ObjectWithDataParamOrReturn(object):
    def __init__(self, object_id, class_id, metadata, obj_bytes):
        """
        Create object with data params or return
        :param object_id: id of the object
        :param class_id: id of the class of the object
        :param metadata: metadata of the object
        :param obj_bytes: object bytes
        """
        self.object_id = object_id
        self.class_id = class_id
        self.metadata = metadata
        self.obj_bytes = obj_bytes
