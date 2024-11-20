import datetime
from uuid import UUID

import jwt

from . import servicer
from .base_classes import MiddlewareBase
from .exceptions import MiddlewareException

__all__ = ["MiddlewareBase", "MiddlewareException"]

import logging

logger = logging.getLogger(__name__)


def jwt_validation(username, token):
    # TODO: Username & password should br required to validate the token
    password = "s3cret"
    try:
        decoded_payload = jwt.decode(token, password, algorithms=["HS256"])
        if decoded_payload.get("username") != username:
            raise Exception("Wrong username")
    except jwt.ExpiredSignatureError as e:
        raise e
    except jwt.InvalidTokenError as e:
        raise e


def generate_jwt(secret_key: str = "", user: str = "dataclay", TOKEN_EXPIRATION: int = 24 * 30):
    # TODO: Store the username & password in a database in order to check it later
    payload = {
        "username": user,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=TOKEN_EXPIRATION),
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token
