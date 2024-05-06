import contextvars
import functools

from dataclay.runtime import get_dc_event_loop


def run_in_context(context: contextvars.Context, callable, *args, **kwargs):
    """Run a callable with a given context"""
    return context.run(callable, *args, **kwargs)


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
