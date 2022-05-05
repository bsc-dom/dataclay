import json
import etcd3

etcd = etcd3.client('localhost', 2379)

def get_classname_and_namespace_for_ds(metaclass_id):
    global etcd
    key = f'/metaclass/{metaclass_id}'
    value = etcd.get(key)
    metaclass = json.loads(value[0])
    return metaclass['name'], metaclass['namespace']