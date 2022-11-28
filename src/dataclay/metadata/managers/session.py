import json
import uuid

from opentelemetry import trace

from dataclay.exceptions.exceptions import *
from dataclay_common.protos import common_messages_pb2
from dataclay.utils.json import UUIDEncoder, uuid_parser

tracer = trace.get_tracer(__name__)


class Session:
    def __init__(self, id, username, dataset_name, is_active=True):
        self.id = id
        self.username = username
        self.dataset_name = dataset_name
        self.is_active = is_active

    def key(self):
        return f"/session/{self.id}"

    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))

    @classmethod
    def from_proto(cls, proto):
        session = cls(
            uuid.UUID(proto.id),
            proto.username,
            proto.dataset_name,
            proto.is_active,
        )
        return session

    def get_proto(self):
        return common_messages_pb2.Session(
            id=str(self.id),
            username=self.username,
            dataset_name=self.dataset_name,
            is_active=self.is_active,
        )


class SessionManager:
    def __init__(self, etcd_client):
        self.etcd_client = etcd_client

    @tracer.start_as_current_span("put_session")
    def put_session(self, session):
        self.etcd_client.put(session.key(), session.value())

    @tracer.start_as_current_span("get_session")
    def get_session(self, session_id):
        """Return Session with session_id."""
        key = f"/session/{session_id}"
        value = self.etcd_client.get(key)[0]
        if value is None:
            raise SessionDoesNotExistError(session_id)

        return Session.from_json(value)

    @tracer.start_as_current_span("exists_session")
    def exists_session(self, session_id):
        """ "Returns ture if the session exists, false otherwise"""

        key = f"/session/{session_id}"
        value = self.etcd_client.get(key)[0]
        return value is not None

    @tracer.start_as_current_span("delete_session")
    def delete_session(self, session_id):
        key = f"/session/{session_id}"
        self.etcd_client.delete(key)
