from uuid import UUID

from dataclay.metadata.kvdata import Session

from .base_classes import MiddlewareBase
from .exceptions import MiddlewareException

from . import servicer

__all__ = [
    "MiddlewareBase", "MiddlewareException"
]


def get_session(request) -> Session:
    """Retrieve Session information from the request.session_id field of the gRPC method."""
    if servicer.global_metadata_api is None:
        raise SystemError("get_session is only available from within a Proxy running environment")

    try:
        session_id = UUID(request.session_id)
    except AttributeError:
        raise ValueError("This method did not have a syntactically valid SessionID")

    return servicer.global_metadata_api.get_session(session_id)
