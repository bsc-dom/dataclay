class PersistentParamOrReturn(object):
    def __init__(self, object_id, hint, class_id):
        """
        :param object_id: id of the object
        :param hint: hint of the object
        :param class_id: id of the class of the object
        """
        self.object_id = object_id
        self.hint = hint
        self.class_id = class_id
