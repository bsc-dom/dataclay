"""Example of using constraints in a method. This is relevant for COMPSs"""

import asyncio
import concurrent.futures
import contextvars
import time

from dataclay import Client
from dataclay.config import constraints_var
from dataclay.contrib.modeltest.compss import CPUIntensiveTask
from storage.api import ConstraintsContext


async def main():

    client = Client(host="127.0.0.1")
    client.start()

    cpu_intensive_task = CPUIntensiveTask()
    await cpu_intensive_task.a_make_persistent()

    ###############
    # BASE Version

    # NOTE: It is also possible to set the contextvar directly instead of using the context manager
    # constraints_var.set({"max_threads": 2})

    with ConstraintsContext({"max_threads": 2}):
        start_time = time.time()
        cpu_intensive_task.cpu_intensive_task()
        end_time = time.time()
        print(f"BASE 1 Task completed in {end_time - start_time:.2f} seconds")

    with ConstraintsContext({"max_threads": 3}):
        start_time = time.time()
        await cpu_intensive_task.a_cpu_intensive_task()
        end_time = time.time()
        print(f"BASE 1 ASync Task completed in {end_time - start_time:.2f} seconds")

    ###############
    # THREAD Version

    with ConstraintsContext({"max_threads": 1}):
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future1 = executor.submit(
                contextvars.copy_context().run, cpu_intensive_task.cpu_intensive_task
            )
            future2 = executor.submit(
                contextvars.copy_context().run, cpu_intensive_task.cpu_intensive_task
            )
            future3 = executor.submit(
                contextvars.copy_context().run, cpu_intensive_task.cpu_intensive_task
            )
            future4 = executor.submit(
                contextvars.copy_context().run, cpu_intensive_task.cpu_intensive_task
            )

            # Wait for tasks to complete
            concurrent.futures.wait([future1, future2, future3, future4])

        end_time = time.time()
        print(f"Task completed in {end_time - start_time:.2f} seconds")

    ###############
    # ASYNC Version
    # WARNING: Never use async activemethods for CPU intensive tasks, as they will block the event loop
    # This is just an example of how to use async activemethods

    with ConstraintsContext({"max_threads": 1}):
        start_time = time.time()
        print("Starting tasks")
        a = asyncio.create_task(cpu_intensive_task.a_cpu_intensive_task())
        b = asyncio.create_task(cpu_intensive_task.a_cpu_intensive_task())
        c = asyncio.create_task(cpu_intensive_task.a_cpu_intensive_task())
        d = asyncio.create_task(cpu_intensive_task.a_cpu_intensive_task())

        await asyncio.gather(a, b, c, d)
        end_time = time.time()
        print(f"Task completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
