import pytest

from dataclay.contrib.modeltest.classes import Box, TextReader


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

    backends[backend_ids[0]].flush_all()
    text_reader.readline()

    assert text_reader.lineno == 1
