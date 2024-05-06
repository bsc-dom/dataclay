from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Union

from dataclay.utils.lockmanager import LockManager

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from dataclay.runtime.backend import BackendRuntime
    from dataclay.runtime.client import ClientRuntime


# Use for context-local data (current session, etc.)
session_var = contextvars.ContextVar("session")

current_runtime: Union[ClientRuntime, BackendRuntime, None] = None

# NOTE: This global event loop is necessary (even if not recommended by asyncio) because
# dataClay methods can be called from different threads (when running activemethods in backend)
# and we need to access the single event loop from the main thread.
dc_event_loop: AbstractEventLoop = None


def get_runtime() -> Union[ClientRuntime, BackendRuntime, None]:
    return current_runtime


def set_runtime(new_runtime: Union[ClientRuntime, BackendRuntime]):
    global current_runtime
    current_runtime = new_runtime


def set_dc_event_loop(loop):
    global dc_event_loop
    dc_event_loop = loop


def get_dc_event_loop() -> Union[None, AbstractEventLoop]:
    return dc_event_loop


lock_manager = LockManager()
