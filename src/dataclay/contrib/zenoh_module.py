"""
dataClay includes support for publisher/subscriber communication via Zenoh.

In order to use this functionality, the client class has to inherit the :class:`ZenohMixin` class. Communications can 
be established using pub/sub and queries. 

The subscriber can specify how the messages will be handled and to which topics it will be subscribed. Also, it 
can ask for the last value stored in an existing subscription using the queries.

The publisher can send messages to a specific topic.

"""

try:
    import zenoh
except ImportError:
    import warnings

    warnings.warn("Warning: <import zenoh> failed", category=ImportWarning)
import logging
import time
from threading import Thread

from dataclay import activemethod

logger = logging.getLogger(__name__)


class ZenohMixin:
    """Zenoh mechanisms"""

    subscriptions: str
    conf: str

    @activemethod
    def __init__(self, conf: str = "{}"):
        """Class constructor.

        Args:
            conf (str, optional): Change the configuration if needed. Defaults to '{}'.
        """
        self.subscriptions = []
        self.conf = conf

    @activemethod
    def handler(self, sample):
        """Placeholder for function handler. This function describes how the client will handle a message.

        Args:
            sample (zenoh.Sample): Information sent by Zenoh to the subscriber.

        Raises:
            NotImplementedError: If the handler function has not been implemented an error is raised.
        """
        raise NotImplementedError("Must override handler")

    @activemethod
    def produce_zenoh_msg(self, buf: str = "", key: str = "dataclay", **more):
        """Sends the message "buf" to the topic "key".

        Args:
            buf (str, optional): Message. Defaults to "".
            key (str, optional): Topic. Defaults to "dataclay".
        """
        session = zenoh.open(zenoh.Config.from_json5(self.conf))
        pub = session.declare_publisher(key)
        pub.put(buf)

    @activemethod
    def send_to_zenoh(self):
        """Previous function to produce_zenoh_msg. Gets all the arguments needed from the calling class."""
        import inspect

        attributes = inspect.getmembers(self.__class__, lambda a: not (inspect.isroutine(a)))
        field_values = {}
        for field in attributes:
            fieldname = field[0]
            if not (fieldname.startswith("_")):
                field_values[fieldname] = getattr(self, fieldname)
        self.produce_zenoh_msg(**field_values)

    @activemethod
    def __receive_data(self, key):
        """While the client is subscribed to a topic, it will check and handle the receipt of a message.

        Args:
            key (str): Topic.
        """
        session = zenoh.open(zenoh.Config.from_json5(self.conf))
        sub = session.declare_subscriber(key, self.handler)
        while key in self.subscriptions:
            time.sleep(0.1)
        return

    @activemethod
    def receive_data(self, key: str = "dataclay"):
        """Create a thread which will check if a message from the topic arrives and will handle it.

        Args:
            key (str): Topic.
        """
        if key not in self.subscriptions:
            t = Thread(target=self.__receive_data, args=(key,))
            self.subscriptions.append(key)
            t.start()

    @activemethod
    def unsubscribe(self, key: str = "dataclay"):
        """Unsubscribes the client from a topic.

        Args:
            key (str): Topic.
        """
        try:
            self.subscriptions.remove(key)
        except:
            logger.error("The client was not subscribed to this topic")

    @activemethod
    def get_last_data(self, key: str = "dataclay"):
        """Returns the latest value stored in this Zenoh topic.

        Args:
            key (str): Topic.

        Returns:
            list[str{reply.key_expr};{reply.playload}]: Latest value stored on a specific Zenoh
            topic.
        """
        returns = []
        session = zenoh.open(zenoh.Config.from_json5(self.conf))
        replies = session.get(key, zenoh.ListCollector())
        for reply in replies():
            try:
                returns.append(
                    "Received ('{}': '{}')".format(
                        reply.ok.key_expr, reply.ok.payload.decode("utf-8")
                    )
                )
            except:
                returns.append("Received (ERROR: '{}')".format(reply.err.payload.decode("utf-8")))
        return returns
