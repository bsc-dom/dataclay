from model.zenohsubs import ZenohSubs
from dataclay import Client
import random

client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

try:
    zenohSub = ZenohSubs.get_by_alias()
except Exception:
    zenohSub = ZenohSubs()
    zenohSub.make_persistent()

zenohSub.set_key("tmp2")
zenohSub.set_buf(str(random.randint(0, 30)))

zenohSub.send_to_zenoh()