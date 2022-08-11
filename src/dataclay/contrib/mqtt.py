"""Basic Synchronization mechanisms."""

from dataclay import dclayMethod

""" Mqtt pool of producers """
MQTT_PRODUCERS = dict()


class MQTTMixin(object):
    """MQTT mechanisms"""

    @dclayMethod(data="dict<str, anything>", topic="str")
    def produce_mqtt_msg(self, data, topic="dataclay"):
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

    @dclayMethod()
    def send_to_mqtt(self):
        import inspect

        attributes = inspect.getmembers(self.__class__, lambda a: not (inspect.isroutine(a)))
        field_values = {}
        for field in attributes:
            fieldname = field[0]
            if not (fieldname.startswith("_")):
                field_values[fieldname] = getattr(self, fieldname)

        self.produce_mqtt_msg(field_values)
