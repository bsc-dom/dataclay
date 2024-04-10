"""
MQTT bridging
=============

dataClay includes support for client communication via MQTT.

In order to use this functionality, the client class has to inherit the MQTTMixin class. The client will be 
able to specify how the messages should be handled, to which topics will be subscribed and send messages with 
a topic. 

"""
from typing import Any

from dataclay import activemethod

import logging

""" Mqtt pool of producers """
MQTT_PRODUCERS = dict()

logger = logging.getLogger(__name__)

class MQTTMixin:
    """MQTT mechanisms"""

    @activemethod
    def message_handling(self,client, userdata, msg):
        """Placeholder for function message_handling. This function describes how the client will handle a 
        message

        Args:
            client (Client): The client instance for this callback
            userdata: The private user data as set in Client() or user_data_set()
            msg (MQTTMessage): The received message.
                        This is a class with members topic, payload, qos, retain.

        Raises:
            NotImplementedError: If the message_handling function has not been implemented an error is raised
        """
        raise NotImplementedError("Must override message_handling")

    @activemethod
    def subscribe_to_topic(self, topic: str = "dataclay"):
        """Subscribes the client to a topic and indicates how will handle a message receiving

        Args:
            topic (str, optional): String representing the topic. Defaults to "dataclay".
        """
        import os
        import paho.mqtt.client as mqtt
        from dataclay.contrib.mqtt import MQTT_PRODUCERS

        mqtt_host = os.getenv("MQTT_HOST", "mqtt5")
        mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        mqtt_client = os.getenv("MQTT_PRODUCER_ID", "dataclay_mqtt_producer")
        mqtt_address = f"{mqtt_host}:{mqtt_port}"
        if mqtt_address in MQTT_PRODUCERS:
            mqtt_producer = MQTT_PRODUCERS[mqtt_address]
        else:
            mqtt_producer = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,mqtt_client)
            mqtt_producer.on_message = self.message_handling
            mqtt_producer.connect(mqtt_host, mqtt_port)
            mqtt_producer.loop_start()
            MQTT_PRODUCERS[mqtt_address] = mqtt_producer
        mqtt_producer.subscribe(topic)

    @activemethod
    def produce_mqtt_msg(self, data: dict[str, Any], topic: str = "dataclay", **more):
        """The client is connected to the broker and it sends a message to the chosen topic

        Args:
            data (dict[str, Any]): Message
            topic (str, optional): Topic of the message. Defaults to "dataclay".
        """
        import os
        from json import dumps
        import paho.mqtt.client as mqtt
        from dataclay.contrib.mqtt import MQTT_PRODUCERS

        mqtt_host = os.getenv("MQTT_HOST", "mqtt5")
        mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        mqtt_client = os.getenv("MQTT_PRODUCER_ID", "dataclay_mqtt_producer")
        mqtt_address = f"{mqtt_host}:{mqtt_port}"
        if mqtt_address in MQTT_PRODUCERS:
            mqtt_producer = MQTT_PRODUCERS[mqtt_address]
        else:
            mqtt_producer = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,mqtt_client)
            mqtt_producer.connect(mqtt_host, mqtt_port)
            mqtt_producer.loop_start()
            MQTT_PRODUCERS[mqtt_address] = mqtt_producer
        data_str = dumps(data).encode("utf-8")
        mqtt_producer.publish(topic, data_str, qos=1)

    @activemethod
    def send_to_mqtt(self):
        """Previous function to produce_mqtt_msg. Gets all the arguments needed from the calling class
        """
        import inspect
        attributes = inspect.getmembers(self.__class__, lambda a: not (inspect.isroutine(a)))
        field_values = {}
        for field in attributes:
            fieldname = field[0]
            if not (fieldname.startswith("_")):
                field_values[fieldname] = getattr(self, fieldname)
        self.produce_mqtt_msg(**field_values)
