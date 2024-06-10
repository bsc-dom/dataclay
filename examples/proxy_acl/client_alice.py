from model.datum import SensorValues

from dataclay import Client

client = Client(proxy_host="127.0.0.1", username="alice", password="s3cret")
client.start()

print(client)

values = SensorValues()

values.make_persistent(alias="demo")

values.add_element(42)

a = values.values

print(a)

values.add_element(43)

print("")
print("**************************")
print("The following should fail:")
print("**************************")
print("Average: %f" % values.public_data())

client.stop()
