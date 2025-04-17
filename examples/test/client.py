import contextvars
from concurrent.futures import ThreadPoolExecutor

from dataclay import Client
from dataclay.contrib.modeltest.family import Dog, Family, Person

client = Client()
client.start()

