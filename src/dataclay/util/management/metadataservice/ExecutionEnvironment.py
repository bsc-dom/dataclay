class ExecutionEnvironment(object):
    def __init__(self, id, hostname, name, port, lang, dataclay_instance_id):
        self.id = id
        self.hostname = hostname
        self.name = name
        self.port = port
        self.lang = lang
        self.dataclay_instance_id = dataclay_instance_id

    def __str__(self):
        return f"[EE/id={self.id}/{self.name}/{self.hostname}:{self.port}/dc_ID={self.dataclay_instance_id}]"
