import json
import logging

from opentelemetry import trace
from passlib.hash import bcrypt

from dataclay.exceptions.exceptions import *
from dataclay.utils.json import UUIDEncoder, uuid_parser

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)


# TODO: Extend class to generic with key(), value(), ...
class Account:
    def __init__(
        self,
        username: str,
        password: str = None,
        hashed_password: str = None,
        role: str = "NORMAL",
        datasets: list = None,
    ):
        self.username = username
        if password is not None:
            self.hashed_password = bcrypt.hash(password)
        else:
            self.hashed_password = hashed_password
        self.role = role
        self.datasets = datasets or []

    def key(self):
        return f"/account/{self.username}"

    def value(self):
        return json.dumps(self.__dict__, cls=UUIDEncoder)

    @classmethod
    def from_json(cls, s):
        return cls(**json.loads(s, object_hook=uuid_parser))

    @tracer.start_as_current_span("verify")
    def verify(self, password, role=None):
        if not bcrypt.verify(password, self.hashed_password):
            return False
        if role is not None and self.role != role:
            return False
        return True


class AccountManager:

    lock = "lock_account"

    def __init__(self, etcd_client):
        self.etcd_client = etcd_client

    @tracer.start_as_current_span("put_account")
    def put_account(self, account):
        self.etcd_client.put(account.key(), account.value())

    @tracer.start_as_current_span("get_account")
    def get_account(self, username):
        # Get account from etcd and checks that it exists
        key = f"/account/{username}"
        value = self.etcd_client.get(key)[0]
        if value is None:
            raise AccountDoesNotExistError(username)

        return Account.from_json(value)

    @tracer.start_as_current_span("exists_account")
    def exists_account(self, username):
        """ "Returns ture if the account exists"""

        key = f"/account/{username}"
        value = self.etcd_client.get(key)[0]
        return value is not None

    @tracer.start_as_current_span("new_account")
    def new_account(self, account):
        """Creates a new account. Checks that the username doesn't exists"""

        with self.etcd_client.lock(self.lock):
            if self.exists_account(account.username):
                raise AccountAlreadyExistError(account.username)
            self.put_account(account)
