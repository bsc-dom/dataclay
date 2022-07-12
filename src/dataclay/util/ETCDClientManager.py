import json
import etcd3

from dataclay.commonruntime.Settings import settings


class ETCDClientManager:
    def __init__(self):
        pass

    def initialize(self):
        self.etcd = etcd3.client(settings.logicmodule_host, 2379)

    def get_metaclass(self, id):
        key = f"/metaclass/{id}"
        value = self.etcd.get(key)[0]
        if value is None:
            raise Exception(f"Metaclass {id} does not exists!")
        # TODO: Create and return a Metaclass object
        return json.loads(value)

    def put_object(self, object):
        # TODO: Create a Object object and use self.__dict__
        key = f"/object/{object.get_object_id()}"
        value = dict()
        value["class_id"] = str(object.get_class_id())
        value["dataset_id"] = str(object.get_dataset_id())
        value["execution_environments"] = [str(ee) for ee in object.get_all_locations().keys()]
        value["is_read_only"] = object.is_read_only()
        value["alias"] = str(object.get_alias())
        value["language"] = "python"
        value["owner"] = str(object.get_owner_session_id())
        value = json.dumps(value)
        self.etcd.put(key, value)

    def get_value(self, key):
        value = self.etcd.get(key)[0]
        if value is None:
            raise Exception(f"Key {key} does not exists!")
        return json.loads(value)

    def put_value(self, key, value):
        self.etcd.put(key, value)


etcdClientMgr = ETCDClientManager()
