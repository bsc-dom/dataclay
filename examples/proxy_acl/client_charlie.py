from model.datum import SensorValues

from dataclay import Client

client = Client(proxy_host="127.0.0.1", username="charlie", password="s3cret", dataset="testdata")
client.start()

values = SensorValues.get_by_alias("demo")

print("")
print("**************************")
print("The following should fail:")
print("**************************")
print("Average: %f" % values.public_data())
