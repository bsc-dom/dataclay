import asyncio
import pytest

import concurrent.futures
from threading import Thread

from dataclay.event_loop import get_dc_event_loop
from dataclay.config import get_runtime

from dataclay.contrib.modeltest.concurrency import PingPong

def test_sync_basic_concurrency(client):
    """
    Test the synchronous execution of nested activemethods
    """
    backends = list(client.get_backends().keys())
    pp1 = PingPong()
    pp1.make_persistent(backend_id=backends[0])
    pp2 = PingPong()
    pp2.make_persistent(backend_id=backends[1])
    pp1.pong_obj = pp2
    pp2.pong_obj = pp1

    # Some low-level asyncio stuff here, because we cannot use Threads and
    # starting a new client instance seems overkill (but would be best, would it?)
    future = asyncio.run_coroutine_threadsafe(
                get_runtime().call_remote_method(pp1, "ping", tuple(), dict()),
                get_dc_event_loop(),
            )

    with pytest.raises(concurrent.futures.TimeoutError):
        future.result(timeout=1)
    
    pp2.ping(wait_event=False)

    pp1.event_set()
    pp2.event_set()

    future.result(timeout=1)
    assert future.done()

def test_sync_high_concurrency(client):
    """
    Test the synchronous execution of nested activemethods
    """
    backends = list(client.get_backends().keys())
    pp1 = PingPong()
    pp1.make_persistent(backend_id=backends[0])
    pp2 = PingPong()
    pp2.make_persistent(backend_id=backends[1])
    pp1.pong_obj = pp2
    pp2.pong_obj = pp1

    future1 = asyncio.run_coroutine_threadsafe(
            get_runtime().call_remote_method(pp1, "ping", (10, True), {}),
            get_dc_event_loop(),
    )

    future2 = asyncio.run_coroutine_threadsafe(
            get_runtime().call_remote_method(pp2, "ping", (10, True), {}),
            get_dc_event_loop(),
    )

    with pytest.raises(concurrent.futures.TimeoutError):
        future1.result(timeout=1)

    with pytest.raises(concurrent.futures.TimeoutError):
        future2.result(timeout=1)

    pp2.ping(wait_event=False)
    pp1.event_set()
    pp2.event_set()

    future1.result(timeout=1)
    future2.result(timeout=1)
    assert future1.done()
    assert future2.done()
