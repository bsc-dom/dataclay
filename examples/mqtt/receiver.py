from model.mqttsubs import MqttSubs

from dataclay import Client

client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

try:
    mqttsub = MqttSubs.get_by_alias("receiver")
except Exception:
    mqttsub = MqttSubs()
    mqttsub.make_persistent(alias="receiver")

mqttsub.set_topic("tmp")

mqttsub.subscribe_to_topic(mqttsub.topic)
