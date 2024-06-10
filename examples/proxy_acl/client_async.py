import asyncio

from model.datum import SensorValues

from dataclay import AsyncClient

# TODO: Still in progress


async def main():
    client = AsyncClient(proxy_host="127.0.0.1", password="s3cret")
    client.start()
    values = SensorValues()
    await values.a_make_persistent(alias="demo")
    values.add_element(42)
    print(values.values)


if __name__ == "__main__":
    asyncio.run(main())
while True:
    pass
