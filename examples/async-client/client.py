import asyncio


from dataclay import AsyncClient
from dataclay.contrib.modeltest.family import Dog, Family, Person


async def main():

    client = AsyncClient(host="127.0.0.1")
    await client.start()

    person = Person("Marc", 24)
    await person.make_persistent()

    # TODO: Failse because it returns a coroutine for attribute access
    # Should be fixed in the future
    print(person.is_persistent)
    print(person.name)


if __name__ == "__main__":
    asyncio.run(main())
