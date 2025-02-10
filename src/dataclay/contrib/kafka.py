"""Basic Synchronization mechanisms."""

import inspect
import os
from json import dumps

from kafka import KafkaProducer

from dataclay import activemethod
from dataclay.contrib.kafka import KAFKA_PRODUCERS

""" Kafka pool of producers """
KAFKA_PRODUCERS = dict()


class KafkaMixin(object):
    """KAFKA mechanisms"""

    @activemethod
    def produce_kafka_msg(self, data, topic="dataclay"):
        """Kafka message producer function

        Args:
            data (_type_): Message
            topic (str, optional): Topic of the message. Defaults to "dataclay".
        """
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

    @activemethod
    def send_to_kafka(self):
        """Previous function to produce_kafka_msg. Gets all the arguments needed from the calling class."""
        attributes = inspect.getmembers(self.__class__, lambda a: not (inspect.isroutine(a)))
        field_values = {}
        for field in attributes:
            fieldname = field[0]
            if not (fieldname.startswith("_")):
                field_values[fieldname] = getattr(self, fieldname)
        self.produce_kafka_msg(field_values)
