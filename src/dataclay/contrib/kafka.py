"""Basic Synchronization mechanisms."""

from dataclay import dclayMethod

class KafkaMixin(object):
    """KAFKA mechanisms
    """

    @dclayMethod(data="dict<str, anything>", topic="str")
    def produce_kafka_msg(self, data, topic="dataclay"):
        import os
        from kafka import KafkaProducer
        from json import dumps
        if not hasattr(self, "producer") or self.producer is None:
            kafka_address = os.getenv('KAFKA_ADDR', 'kafka:9092')
            self.producer = KafkaProducer(bootstrap_servers=[kafka_address],
                                          value_serializer=lambda x:
                                          dumps(x).encode('utf-8'))
        self.producer.send(topic, value=data)

    @dclayMethod()
    def send_to_kafka(self):
        import inspect

        attributes = inspect.getmembers(self.__class__, lambda a:not(inspect.isroutine(a)))
        field_values = {}
        for field in attributes:
            fieldname = field[0]
            if not(fieldname.startswith('_')):
                field_values[fieldname]=getattr(self, fieldname)

        self.produce_kafka_msg(field_values)