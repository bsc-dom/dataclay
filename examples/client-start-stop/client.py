from dataclay import Client
from dataclay.contrib.modeltest.family import Person

print("############")
print("#New client#")
print("############")
client = Client(host="127.0.0.1", username="testuser", password="s3cret", dataset="testdata")
client.start()

person = Person("Marc", 24)
person.make_persistent("Marc")
print("//Age:", person.age)
person.add_year()
print("#################")
print("#Stopping client#")
print("#################")
client.stop()

try:
    print("//Age:", person.age)
except Exception as e:
    print("Exception:", str(e))

try:
    person.add_year()
except Exception as e:
    print("Exception:", str(e))

print("############")
print("#New client#")
print("############")
client1 = Client(host="127.0.0.1", username="testuser1", password="s3cret1", dataset="testdata1")
client1.start()

print("//Age:", person.age)
person.add_year()
print("//Age:", person.age)
