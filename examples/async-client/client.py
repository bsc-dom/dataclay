import asyncio

from dataclay import Client
from dataclay.contrib.modeltest.family import Dog, Family, Person


async def main():

    client = Client(host="127.0.0.1")
    client.start()

    person = Person("Marc", 24)
    print(person.name)

    await person.a_make_persistent()

    print(person.is_persistent)
    print(person.name)

    print(await client.a_get_backends())


if __name__ == "__main__":
    asyncio.run(main())
