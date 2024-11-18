from dataclay.contrib.modeltest.classes import Box, TextReader
from dataclay.event_loop import run_dc_coroutine


def test_getstate(client):
    text_reader = TextReader("testfile")
    text_reader.readline()
    assert text_reader.lineno == 1

    text_reader.make_persistent()
    text_reader.readline()
    assert text_reader.lineno == 2


def test_getstate_v2(client):
    box = Box()
    box.value = TextReader("testfile")
    box.value.readline()
    assert box.value.lineno == 1

    box.make_persistent()
    assert box.value.lineno == 1
    box.value.readline()
    assert box.value.lineno == 2


def test_getstate_unload(client):
    backends = client.get_backends()
    backend_ids = list(backends)

    text_reader = TextReader("testfile")
    text_reader.make_persistent(backend_id=backend_ids[0])

    run_dc_coroutine(backends[backend_ids[0]].flush_all)
    text_reader.readline()

    assert text_reader.lineno == 1


def test_getstate_unload_v2(client):
    backends = client.get_backends()
    backend_ids = list(backends)

    box = Box()
    box.value = TextReader("testfile")
    box.make_persistent(backend_id=backend_ids[0])

    run_dc_coroutine(backends[backend_ids[0]].flush_all)
    box.value.readline()
    assert box.value.lineno == 1


def test_getstate_move(client):
    """Test move to new backend"""
    backend_ids = list(client.get_backends())

    text_reader = TextReader("testfile")
    text_reader.make_persistent(backend_id=backend_ids[0])
    text_reader.readline()

    text_reader.move(backend_ids[1])
    text_reader.readline()
    assert text_reader.lineno == 2


def test_getstate_move_box(client):
    """Test move to new backend"""
    backend_ids = list(client.get_backends())

    box = Box()
    box.value = TextReader("testfile")
    box.make_persistent(backend_id=backend_ids[0])
    box.value.readline()

    box.move(backend_ids[1])
    box.value.readline()
    assert box.value.lineno == 2


def test_getstate_move_box_recursive(client):
    """Test move to new backend"""
    backend_ids = list(client.get_backends())

    box = Box()
    box.value = TextReader("testfile")
    box.make_persistent(backend_id=backend_ids[0])
    box.value.readline()

    box.move(backend_ids[1], recursive=True)
    box.value.readline()
    assert box.value.lineno == 2
