import datetime
from uuid import UUID

import jwt

from . import servicer
from .base_classes import MiddlewareBase
from .exceptions import MiddlewareException

__all__ = ["MiddlewareBase", "MiddlewareException"]

import logging

logger = logging.getLogger(__name__)


def get_session(request):
    raise Exception("This method should be replaced by jwt token validation in the future.")
    """Retrieve Session information from the request.session_id field of the gRPC method."""
    if servicer.global_metadata_api is None:
        raise SystemError("get_session is only available from within a Proxy running environment")

    try:
        session_id = UUID(request.session_id)
    except AttributeError:
        raise ValueError("This method did not have a syntactically valid SessionID")

    return servicer.global_metadata_api.get_session(session_id)


def generate_jwt(secret_key: str = "", user: str = "dataclay", TOKEN_EXPIRATION: int = 24 * 30):
    # TODO: Store the username & password in a database in order to check it later
    payload = {
        "username": user,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=TOKEN_EXPIRATION),
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token


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
