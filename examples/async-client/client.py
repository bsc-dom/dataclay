import asyncio

from dataclay import AsyncClient
from dataclay.contrib.modeltest.family import Dog, Family, Person


async def main():

    client = AsyncClient(host="127.0.0.1")
    client.start()

    person = Person("Marc", 24)
    print(person.name)

    await person.a_make_persistent()

    # TODO: Failse because it returns a coroutine for attribute access
    # Should be fixed in the future
    print(person.is_persistent)
    print(await person.name)

    print(await client.get_backends())


if __name__ == "__main__":
    asyncio.run(main())
