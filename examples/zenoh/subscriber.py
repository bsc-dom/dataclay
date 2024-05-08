from model.zenohsubs import ZenohSubs

from dataclay import Client

client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

try:
    zenohSub = ZenohSubs.get_by_alias("subs")
except Exception:
    zenohSub = ZenohSubs()
    zenohSub.make_persistent(alias="subs")

zenohSub.set_key("tmp")

zenohSub.get_last_data(zenohSub.key)

zenohSub.receive_data(zenohSub.key)
