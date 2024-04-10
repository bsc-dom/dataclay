from dataclay import DataClayObject, activemethod
from dataclay.contrib.mqtt import MQTTMixin
import logging
from typing import Any

logger = logging.getLogger(__name__)

class MqttSubs(DataClayObject,MQTTMixin):

    data: dict[str, Any]
    topic: str
    temperature: str

    @activemethod
    def __init__(self):
        self = self
        self.data=""
        self.topic=""
        self.temperature="NO DATA"

    @activemethod
    def message_handling(self,client, userdata, msg):
        from json import loads
        tmp = loads(msg.payload.decode())
        #self.data = tmp
        int_tmp = int(tmp)
        if(int_tmp<5):
            self.temperature = "freezing(" + tmp + ")"
        else:
            if(int_tmp<17):
                self.temperature = "cold(" + tmp + ")"
            else:
                self.temperature = "warm(" + tmp + ")"
        
        logger.debug("Temperature is %s (%s)",self.temperature, tmp)

    @activemethod
    def set_topic(self, topic):
        self.topic = topic

    @activemethod
    def set_data(self, data):
        self.data = data

    @activemethod
    def get_temp(self):
        return self.temperature