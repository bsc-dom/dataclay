import contextvars
from concurrent.futures import ThreadPoolExecutor

from dataclay import Client
from dataclay.config import get_runtime
from dataclay.contrib.modeltest.family import Dog, Family, Person

client = Client(host="127.0.0.1")
client.start()

current_context = contextvars.copy_context()


def job(name, age):
    person = Person(name, age)
    person.make_persistent()


with ThreadPoolExecutor() as executor:
    for i in range(10):
        future = executor.submit(current_context.run, job, f"Name{i}", i)
        print(future.result())

# person.add_year()
