"""
MQTT bridging
=============

Documentation WIP (moreover, the mixin class has yet to be tested in dataClay 3.x).
"""
from typing import Any

from dataclay import activemethod

""" Mqtt pool of producers """
MQTT_PRODUCERS = dict()


class MQTTMixin:
    """MQTT mechanisms"""

    @activemethod
    def produce_mqtt_msg(self, data: dict[str, Any], topic: str = "dataclay"):
        import os
        from json import dumps

        import paho.mqtt.client as mqtt

        from dataclay.contrib.mqtt import MQTT_PRODUCERS

        mqtt_host = os.getenv("MQTT_HOST", "mqtt")
        mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        mqtt_client = os.getenv("MQTT_PRODUCER_ID", "dataclay_mqtt_producer")
        mqtt_address = f"{mqtt_host}:{mqtt_port}"
        if mqtt_address in MQTT_PRODUCERS:
            mqtt_producer = MQTT_PRODUCERS[mqtt_address]
        else:
            mqtt_producer = mqtt.Client(mqtt_client)
            mqtt_producer.connect(mqtt_host, mqtt_port)
            mqtt_producer.loop_start()
            MQTT_PRODUCERS[mqtt_address] = mqtt_producer
        data_str = dumps(data).encode("utf-8")
        mqtt_producer.publish(topic, data_str, qos=1)

    @activemethod
    def send_to_mqtt(self):
        import inspect

        attributes = inspect.getmembers(self.__class__, lambda a: not (inspect.isroutine(a)))
        field_values = {}
        for field in attributes:
            fieldname = field[0]
            if not (fieldname.startswith("_")):
                field_values[fieldname] = getattr(self, fieldname)

        self.produce_mqtt_msg(field_values)
