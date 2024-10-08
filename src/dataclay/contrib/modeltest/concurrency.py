import time

from dataclay import DataClayObject, activemethod


class PingPong(DataClayObject):
    _event: bool
    pong_obj: 'PingPong'

    def __init__(self):
        self._event = False
        self.pong_obj = None

    @activemethod
    def event_set(self):
        self._event = True

    @activemethod
    def ping(self, chain=1, wait_event=True):
        if chain > 0 and self.pong_obj is not None:
            self.pong_obj.ping(chain - 1, wait_event)
        if wait_event:
            while not self._event:
                time.sleep(1)
