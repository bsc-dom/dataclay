MQTT 
====

This example explains in a simple way how two clients can communicate with each other using mqtt.
One client, called sender.py, will generate a random temperature value simulating a thermometer. We will also
have another client, called receiver.py, which will be subscribed to the topic "tmp". 
The sender client will send the temperature value to the broker with the topic "tmp". This will trigger the
reciever message_handler() function, which will categorize the temperature between 3 different options:
freezing, cold or warm. 

.. note::
    This example is available in `GitHub <https://github.com/bsc-dom/dataclay/tree/main/examples/mqtt>`_.

Class definition:
The message_handler() function will overwritte the one from the class MQTTMixin at `dataclay.contrib.mqtt`_

.. _dataclay.contrib.mqtt: https://github.com/bsc-dom/dataclay/blob/main/src/dataclay/contrib/mqtt.py

.. literalinclude:: /../examples/mqtt/model/mqttsubs.py
   :language: python
   :caption: mqttsubs.py

Mosquitto configuration: 
In this example we will be using the mosquitto broker with the lowest level of configuration.

.. literalinclude:: /../examples/mqtt/config/mosquitto.conf
   :language: configuration
   :caption: mosquitto.conf

Then we can deploy dataclay using docker-compose. 
Create a file docker-compose.yml and use the following docker-compose file using `docker-compose up`.
You can modify the environment variables MQTT_HOST, MQTT_PORT and MQTT_PRODUCER_ID


.. literalinclude:: /../examples/mqtt/docker-compose.yml
   :language: yaml
   :caption: docker-compose.yml

Then we can run the receiver client application:

.. literalinclude:: /../examples/mqtt/receiver.py
   :language: python
   :caption: receiver.py

And run the sender client application:

.. literalinclude:: /../examples/mqtt/sender.py
   :language: python
   :caption: sender.py

If we leave our receiver.py application running and we call the function "mqttsub.get_temp()", we will get
the temperature which the thermometer sent.