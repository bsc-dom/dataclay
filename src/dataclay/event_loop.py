import asyncio
import contextvars
import functools
import threading
from asyncio import AbstractEventLoop
from typing import Awaitable, Union

# NOTE: This global event loop is necessary (even if not recommended by asyncio) because
# dataClay methods can be called from different threads (when running activemethods in backend)
# and we need to access the single event loop from the main thread.
dc_event_loop: AbstractEventLoop = None


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


# Based on asyncio.to_thread
async def dc_to_thread(func, /, *args, **kwargs):
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
    return await loop.run_in_executor(None, func_call)
