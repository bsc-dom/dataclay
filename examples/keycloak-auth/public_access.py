import asyncio
from dataclay import Client
from dataclay.contrib.modeltest.family import Person

async def main():
    client = Client(proxy_host="127.0.0.1", username="testuser", password="s3cret", dataset="public_dataset")
    client.start()

    person = Person("testuser", 5)

    person.make_persistent(alias="testuser")

    print("Age: ",person.age)

    person.add_year()

    print("#Next year#")

    age = person.age

    print("Age: ",age)


if __name__ == "__main__":
    asyncio.run(main())

