import logging

from dataclay import DataClayObject, activemethod
from dataclay.contrib.zenoh_module import ZenohMixin

logger = logging.getLogger(__name__)


class ZenohSubs(DataClayObject, ZenohMixin):

    data: str
    buf: str
    key: str

    @activemethod
    def __init__(self, conf):
        super().__init__(conf)
        self = self
        self.data = ""
        self.buf = ""
        self.key = ""

    @activemethod
    def handler(self, sample):
        self.data = (
            f"Received {sample.kind} ('{sample.key_expr}': '{sample.payload.decode('utf-8')}')"
        )
        logger.debug(self.data)

    @activemethod
    def set_buf(self, buf):
        self.buf = buf

    @activemethod
    def set_key(self, key):
        self.key = key

    @activemethod
    def get_data(self):
        return self.data
