from dataclay.contrib.modeltest.family import Person
from dataclay import Client

client = Client(proxy_host="127.0.0.1", username="user", password="user",dataset="custom_dataset")
client.start()


person = Person("user", 5)

person.make_persistent(alias="user")

print("Age: ",person.age)

person.add_year()

print("#Next year#")

age = person.age

print("Age: ",age)