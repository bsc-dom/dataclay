"""Basic Synchronization mechanisms."""

from dataclay import dclayMethod

""" Kafka pool of producers """
KAFKA_PRODUCERS = dict()


class KafkaMixin(object):
    """KAFKA mechanisms"""

    @dclayMethod(data="dict<str, anything>", topic="str")
    def produce_kafka_msg(self, data, topic="dataclay"):
        import os
        from json import dumps

        from kafka import KafkaProducer

        from dataclay.contrib.kafka import KAFKA_PRODUCERS

        kafka_address = os.getenv("KAFKA_ADDR", "kafka:9092")
        if kafka_address in KAFKA_PRODUCERS:
            kafka_producer = KAFKA_PRODUCERS[kafka_address]
        else:
            kafka_producer = KafkaProducer(
                bootstrap_servers=[kafka_address],
                value_serializer=lambda x: dumps(x).encode("utf-8"),
            )
            KAFKA_PRODUCERS[kafka_address] = kafka_producer
        kafka_producer.send(topic, value=data)

    @dclayMethod()
    def send_to_kafka(self):
        import inspect

        attributes = inspect.getmembers(self.__class__, lambda a: not (inspect.isroutine(a)))
        field_values = {}
        for field in attributes:
            fieldname = field[0]
            if not (fieldname.startswith("_")):
                field_values[fieldname] = getattr(self, fieldname)

        self.produce_kafka_msg(field_values)
