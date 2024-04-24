Zenoh 
=====

This example explains in a simple way how a publisher and a subscriber can communicate with each other using
Zenoh.
The publisher will generate a random temperature value simulating a thermometer and will send this value to
the topic "tmp". We will then run the subscriber, which first will ask zenoh which is the last value for the
topic "tmp". Later the subscriber will subscribe itself to the topic "key". We will run again the publisher which 
will generate a new temperature value and we will see how the subscriber handles it.


.. note::
    This example is available in `GitHub <https://github.com/bsc-dom/dataclay/tree/main/examples/zenoh>`_.

Class definition:
The handler() function will overwritte the one from the class ZenohMixin at `dataclay.contrib.zenoh`_

.. _dataclay.contrib.zenoh: https://github.com/bsc-dom/dataclay/blob/main/src/dataclay/contrib/zenoh.py

.. literalinclude:: /../examples/zenoh/model/zenohsubs.py
   :language: python
   :caption: zenohsubs.py

Zenoh configuration: 
In this example we will be using a configuration which will let Zenoh store the last value of each topic.

.. literalinclude:: /../examples/zenoh/zenoh_docker/zenoh-conf.json5
   :language: json5
   :caption: zenoh-conf.json5

Then we can deploy dataclay using docker-compose. 
Create a file docker-compose.yml and use the following docker-compose file using `docker-compose up`.


.. literalinclude:: /../examples/zenoh/docker-compose.yml
   :language: yaml
   :caption: docker-compose.yml

Then we can run the publisher(sensor) code:

.. literalinclude:: /../examples/zenoh/sensor.py
   :language: python
   :caption: sensor.py

Run the subscriber code:

.. literalinclude:: /../examples/zenoh/subscriber.py
   :language: python
   :caption: subscriber.py

And run the sensor code again

If we leave our subscriber.py application running and we call the function "zenoh.get_data()", we will get
the temperature which the thermometer sent.