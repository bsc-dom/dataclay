from model.mqttsubs import MqttSubs
from dataclay import Client
import random

client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

try:
    mqttsub = MqttSubs.get_by_alias("sender")
except Exception:
    mqttsub = MqttSubs()
    mqttsub.make_persistent(alias="sender")

mqttsub.set_topic("tmp")

mqttsub.set_data(str(random.randint(0, 30)))

mqttsub.send_to_mqtt()
