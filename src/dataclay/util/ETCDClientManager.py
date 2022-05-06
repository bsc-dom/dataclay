import json
import etcd3

from dataclay.commonruntime.Settings import settings

class ETCDClientManager:

    def __init__(self):
        pass

    def initialize(self):
        self.etcd = etcd3.client(settings.logicmodule_host, 2379)

    def get_classname_and_namespace_for_ds(self, metaclass_id):
        key = f'/metaclass/{metaclass_id}'
        value = self.etcd.get(key)
        metaclass = json.loads(value[0])
        return metaclass['name'], metaclass['namespace']

etcdClientMgr = ETCDClientManager()