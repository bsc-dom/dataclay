import asyncio
import concurrent.futures
import contextvars
import functools
import threading
from asyncio import AbstractEventLoop
from typing import Awaitable, Union

import psutil

from dataclay.config import settings

# NOTE: This global event loop is necessary (even if not recommended by asyncio) because
# dataClay methods can be called from different threads (when running activemethods in backend)
# and we need to access the single event loop from the main thread.
dc_event_loop: AbstractEventLoop = None

# Get available CPUs after numactl restriction
cpu_count = len(psutil.Process().cpu_affinity())
# For CPU-bound tasks, use the number of CPUs available
cpu_bound_executor = concurrent.futures.ThreadPoolExecutor(max_workers=cpu_count)
# For I/O-bound tasks, use a higher multiplier
io_bound_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=cpu_count * settings.io_bound_multiplier
)


def set_dc_event_loop(loop):
    global dc_event_loop
    dc_event_loop = loop


def get_dc_event_loop() -> Union[None, AbstractEventLoop]:
    return dc_event_loop


class EventLoopThread(threading.Thread):
    def __init__(self, loop):
        super().__init__(daemon=True, name="EventLoopThread")
        self.loop = loop
        self.ready = threading.Event()

    def run(self):
        print("Starting event loop in new thread")
        self.ready.set()
        self.loop.run_forever()
        print("Event loop stopped")


def run_dc_coroutine(func: Awaitable, *args, **kwargs):
    loop = get_dc_event_loop()
    future = asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)
    return future.result()


# Shared helper to run the function in the executor. Based on asyncio.to_thread
async def _dc_to_thread(func, executor, *args, **kwargs):
    """Asynchronously run function *func* in a separate thread.
    Any *args and **kwargs supplied for this function are directly passed
    to *func*. Also, the current :class:`contextvars.Context` is propogated,
    allowing context variables from the main thread to be accessed in the
    separate thread.
    Return a coroutine that can be awaited to get the eventual result of *func*.
    """
    loop = get_dc_event_loop()
    ctx = contextvars.copy_context()
    func_call = functools.partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(executor, func_call)


# For CPU-bound tasks
async def dc_to_thread_cpu(func, /, *args, **kwargs):
    """Asynchronously run function *func* in a separate thread using the CPU-bound executor."""
    return await _dc_to_thread(func, cpu_bound_executor, *args, **kwargs)


# For I/O-bound tasks
async def dc_to_thread_io(func, /, *args, **kwargs):
    """Asynchronously run function *func* in a separate thread using the I/O-bound executor."""
    return await _dc_to_thread(func, io_bound_executor, *args, **kwargs)
