from model.datum import SensorValues

from dataclay import Client

client = Client(proxy_host="127.0.0.1", username="testuser", password="s3cret")
client.start()

values = SensorValues.get_by_alias("demo")

print("")
print("***********************")
print("Everything should work:")
print("***********************")

values.values = [47]
values.add_element(44)
values.add_element(45)
print("Average: %f" % values.public_data())
print("Internal data: %s" % (values.values,))
