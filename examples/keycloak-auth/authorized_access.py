from dataclay.contrib.modeltest.family import Person
from dataclay import Client

client = Client(proxy_host="127.0.0.1", username="user", password="user",dataset="custom_dataset")
client.start()

client.set_mw_path("/healtgfds")
client.per_mi("Pf9DSDdXD0YXN6oH3GRtdMu1qHGI3wSU")
#client.set_mw_token("dsqdsa")

person = Person("user", 5)

person.make_persistent(alias="user")

print("Age: ",person.age)

person.add_year()

print("#Next year#")

age = person.age

print("Age: ",age)

